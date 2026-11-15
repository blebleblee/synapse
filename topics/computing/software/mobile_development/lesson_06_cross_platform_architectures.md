# Lesson 6: Cross-Platform Architectures

## 1. First-Principles Intuition & Invariants

The cross-platform mobile development problem emerges from a fundamental mismatch between business logic stability and platform API volatility. Business rules—validation logic, domain models, workflow orchestration—evolve on product timelines measured in quarters or years, while iOS and Android platform APIs shift with annual OS releases, deprecation cycles, and hardware capability expansion. Engineering organizations face a stark choice: duplicate business logic across platform-specific codebases, accepting the maintenance burden and divergence risk, or architect a shared core that executes identically on both platforms while exposing platform-specific capabilities through carefully designed abstraction boundaries.

The physical reality of mobile execution provides the invariant constraints. Both iOS and Android devices run on ARM64 processors with hierarchical memory systems, virtual memory management, and strict process isolation enforced by the operating system kernel. iOS applications execute within a Mach-based kernel environment where Objective-C and Swift code compiles to native ARM64 machine code through LLVM. Android applications historically ran on Dalvik bytecode, but modern Android uses ART (Android Runtime) with ahead-of-time compilation to native code, though the Java/Kotlin layer still mediates between application logic and Linux kernel system calls. These architectural differences create the cross-platform challenge: shared business logic must either compile to multiple native targets or execute within a runtime environment that itself bridges these platform differences.

Three canonical approaches emerged from this constraint space, each making different tradeoffs in the performance-portability-complexity triangle. The first approach, native module integration, compiles shared logic to native libraries that each platform loads through foreign function interfaces—C or C++ compiled to ARM64 shared objects (`.so` on Android, `.dylib` on iOS) that expose stable ABI boundaries. The second approach, JavaScript bridge architectures like React Native, executes shared logic in a JavaScript VM while routing UI operations and platform API calls through asynchronous message queues to native code. The third approach, ahead-of-time compilation frameworks like Flutter and Kotlin Multiplatform Mobile, compiles a single language codebase to platform-specific native binaries, either targeting LLVM IR or generating platform-appropriate bytecode/machine code.

The invariant that governs all successful cross-platform architectures is interface stability under platform evolution. Platform vendors (Apple and Google) maintain backwards compatibility in their C-level APIs far more reliably than in higher-level frameworks. Darwin's `libSystem.dylib` and Android's Bionic libc provide stable system call wrappers that persist across OS versions. Graphics APIs like Metal and Vulkan evolve through versioned extensions rather than breaking changes. Network stacks expose BSD socket interfaces that remain constant. A well-designed cross-platform architecture therefore roots its platform abstraction layer in these stable C-level contracts rather than higher-level framework APIs that churn with each OS release.

Memory management semantics create the deepest cross-platform challenge. iOS uses Automatic Reference Counting where the compiler inserts retain/release calls at compile time, creating deterministic deallocation when reference counts reach zero. Android's ART uses tracing garbage collection with concurrent mark-sweep phases, introducing non-deterministic pause times and object lifetime unpredictability. Shared business logic written in C++ with manual memory management or Rust with ownership-based deallocation must bridge to both memory models without introducing leaks or use-after-free vulnerabilities. The bridge layer becomes responsible for lifetime management—retaining objects when crossing into iOS's ARC world, creating global references when passing objects to Android's JNI, and carefully orchestrating deallocation to prevent dangling pointers in either runtime.

Threading models compound the memory management challenge. iOS dispatch queues and Android's Handler/Looper mechanisms both implement message-passing concurrency, but with different scheduling guarantees and different rules for thread-local storage. Shared logic that performs computation on background threads must carefully marshal data across thread boundaries, respecting each platform's main-thread enforcement for UI operations. The cross-platform architecture must either enforce a single threading model across both platforms—typically actors or message-passing rather than shared-memory concurrency—or provide platform-specific threading adapters that map the shared logic's concurrency model to each platform's native primitives.

Build system unification represents the final invariant. iOS builds use Xcode's build system (derived from LLVM/Clang with xcbuild orchestration), consuming `.xcodeproj` files that specify targets, schemes, build phases, and code signing. Android builds use Gradle with the Android Gradle Plugin, consuming Groovy or Kotlin DSL build scripts that declare dependencies, build types, and product flavors. A cross-platform architecture must either generate both project formats from a shared specification or introduce a meta-build system (CMake, Bazel, Buck2) that outputs platform-specific build artifacts. The build unification must handle not just compilation but also resource bundling, code signing, symbol stripping, and the platform-specific final packaging (IPA for iOS, APK/AAB for Android).

## 2. Core Architecture & Mechanics

The native module integration pattern establishes the most direct path to cross-platform code sharing by compiling business logic to shared libraries that both iOS and Android load through stable C ABI boundaries. This approach minimizes runtime overhead—shared code executes as native ARM64 instructions without interpretation or JIT compilation—and provides deterministic performance characteristics. The architecture splits into three layers: the shared core in C, C++, or Rust; platform-specific bindings that expose the shared core to Swift/Objective-C and Java/Kotlin; and platform-specific UI and framework integration that consumes the shared logic through these bindings.

The shared core library must expose a pure C API even if internally implemented in C++ or Rust. C provides the only stable ABI that both iOS and Android FFI mechanisms can consume reliably. A typical shared library header defines opaque pointer types for objects, constructor/destructor functions, and method-like functions that accept the opaque pointers as their first parameter, simulating object-oriented dispatch without C++ name mangling or Rust's trait resolution:

```c
// shared_core.h
#ifndef SHARED_CORE_H
#define SHARED_CORE_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Opaque types - actual definitions in implementation
typedef struct UserSession UserSession;
typedef struct ValidationResult ValidationResult;

// Session lifecycle
UserSession* user_session_create(const char* user_id);
void user_session_destroy(UserSession* session);

// Business logic operations
ValidationResult* user_session_validate_email(
    UserSession* session,
    const char* email
);

bool validation_result_is_valid(const ValidationResult* result);
const char* validation_result_get_error(const ValidationResult* result);
void validation_result_destroy(ValidationResult* result);

// Callback registration for async operations
typedef void (*SessionCallback)(void* context, const char* result);
void user_session_fetch_profile_async(
    UserSession* session,
    SessionCallback callback,
    void* context
);

#ifdef __cplusplus
}
#endif

#endif // SHARED_CORE_H
```

The implementation layer can leverage C++ or Rust for internal logic while maintaining the C boundary. A C++ implementation would use the Pimpl idiom to hide implementation details behind the opaque pointers, with the C functions serving as thin wrappers around C++ method calls:

```cpp
// shared_core.cpp
#include "shared_core.h"
#include <string>
#include <regex>
#include <memory>
#include <thread>

// Internal C++ implementation
class UserSessionImpl {
private:
    std::string user_id_;
    
public:
    explicit UserSessionImpl(std::string user_id)
        : user_id_(std::move(user_id)) {}
    
    struct ValidationResultImpl {
        bool valid;
        std::string error_message;
    };
    
    std::unique_ptr<ValidationResultImpl> validate_email(
        const std::string& email
    ) {
        auto result = std::make_unique<ValidationResultImpl>();
        
        // RFC 5322 simplified pattern
        std::regex pattern(
            R"(^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$)"
        );
        
        result->valid = std::regex_match(email, pattern);
        if (!result->valid) {
            result->error_message = "Invalid email format";
        }
        
        return result;
    }
    
    void fetch_profile_async(
        SessionCallback callback,
        void* context
    ) {
        // Simulate async network operation
        std::thread([this, callback, context]() {
            // In production: actual HTTP request
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            
            std::string result = R"({"name":"User","id":")" 
                + user_id_ + R"("})";
            
            callback(context, result.c_str());
        }).detach();
    }
};

// C API implementation - lifecycle management
UserSession* user_session_create(const char* user_id) {
    try {
        return reinterpret_cast<UserSession*>(
            new UserSessionImpl(user_id)
        );
    } catch (...) {
        return nullptr;
    }
}

void user_session_destroy(UserSession* session) {
    delete reinterpret_cast<UserSessionImpl*>(session);
}

// C API implementation - operations
ValidationResult* user_session_validate_email(
    UserSession* session,
    const char* email
) {
    auto impl = reinterpret_cast<UserSessionImpl*>(session);
    auto result = impl->validate_email(email);
    return reinterpret_cast<ValidationResult*>(result.release());
}

bool validation_result_is_valid(const ValidationResult* result) {
    auto impl = reinterpret_cast<
        const UserSessionImpl::ValidationResultImpl*
    >(result);
    return impl->valid;
}

const char* validation_result_get_error(const ValidationResult* result) {
    auto impl = reinterpret_cast<
        const UserSessionImpl::ValidationResultImpl*
    >(result);
    return impl->error_message.c_str();
}

void validation_result_destroy(ValidationResult* result) {
    delete reinterpret_cast<UserSessionImpl::ValidationResultImpl*>(
        result
    );
}

void user_session_fetch_profile_async(
    UserSession* session,
    SessionCallback callback,
    void* context
) {
    auto impl = reinterpret_cast<UserSessionImpl*>(session);
    impl->fetch_profile_async(callback, context);
}
```

The iOS bridge wraps the C API in Swift-friendly classes that manage memory through ARC and expose idiomatic Swift interfaces. The bridge must carefully manage the lifetime of C objects, retaining them until the Swift wrapper deallocates:

```swift
// UserSession.swift
import Foundation

// Private C API import
private func user_session_create_bridge(
    _ userId: UnsafePointer<CChar>
) -> OpaquePointer? {
    return user_session_create(userId)
}

private func user_session_destroy_bridge(_ session: OpaquePointer) {
    user_session_destroy(session)
}

class UserSession {
    private let handle: OpaquePointer
    
    init(userId: String) {
        guard let handle = userId.withCString({ cString in
            user_session_create_bridge(cString)
        }) else {
            fatalError("Failed to create user session")
        }
        self.handle = handle
    }
    
    deinit {
        user_session_destroy_bridge(handle)
    }
    
    struct EmailValidation {
        let isValid: Bool
        let errorMessage: String?
    }
    
    func validateEmail(_ email: String) -> EmailValidation {
        let resultPtr = email.withCString { cString in
            user_session_validate_email(handle, cString)
        }
        
        guard let result = resultPtr else {
            return EmailValidation(
                isValid: false,
                errorMessage: "Internal error"
            )
        }
        
        defer { validation_result_destroy(result) }
        
        let isValid = validation_result_is_valid(result)
        let errorPtr = validation_result_get_error(result)
        let error = errorPtr != nil ? String(cString: errorPtr!) : nil
        
        return EmailValidation(isValid: isValid, errorMessage: error)
    }
    
    func fetchProfile() async throws -> [String: Any] {
        return try await withCheckedThrowingContinuation { continuation in
            // Context pointer to capture continuation
            let contextPtr = Unmanaged.passRetained(
                continuation as AnyObject
            ).toOpaque()
            
            let callback: @convention(c) (
                UnsafeMutableRawPointer?,
                UnsafePointer<CChar>?
            ) -> Void = { context, resultCString in
                guard let ctx = context,
                      let cString = resultCString else {
                    return
                }
                
                let cont = Unmanaged<AnyObject>
                    .fromOpaque(ctx)
                    .takeRetainedValue() as! 
                    CheckedContinuation<[String: Any], Error>
                
                let jsonString = String(cString: cString)
                
                do {
                    if let data = jsonString.data(using: .utf8),
                       let json = try JSONSerialization.jsonObject(
                           with: data
                       ) as? [String: Any] {
                        cont.resume(returning: json)
                    } else {
                        cont.resume(throwing: 
                            NSError(domain: "Parse", code: -1)
                        )
                    }
                } catch {
                    cont.resume(throwing: error)
                }
            }
            
            user_session_fetch_profile_async(
                handle,
                callback,
                contextPtr
            )
        }
    }
}
```

The Android bridge uses JNI to connect Java/Kotlin to the native library. JNI requires careful lifetime management through global references and explicit attachment of native threads to the JVM when callbacks execute on background threads:

```kotlin
// UserSession.kt
package com.example.shared

class UserSession(userId: String) {
    private val nativeHandle: Long
    
    init {
        nativeHandle = nativeCreate(userId)
        if (nativeHandle == 0L) {
            throw IllegalStateException("Failed to create native session")
        }
    }
    
    protected fun finalize() {
        if (nativeHandle != 0L) {
            nativeDestroy(nativeHandle)
        }
    }
    
    data class EmailValidation(
        val isValid: Boolean,
        val errorMessage: String?
    )
    
    fun validateEmail(email: String): EmailValidation {
        return nativeValidateEmail(nativeHandle, email)
    }
    
    suspend fun fetchProfile(): Map<String, Any> = 
        kotlinx.coroutines.suspendCoroutine { continuation ->
            nativeFetchProfileAsync(nativeHandle) { resultJson ->
                try {
                    val json = org.json.JSONObject(resultJson)
                    val map = mutableMapOf<String, Any>()
                    json.keys().forEach { key ->
                        map[key] = json.get(key)
                    }
                    continuation.resumeWith(Result.success(map))
                } catch (e: Exception) {
                    continuation.resumeWith(Result.failure(e))
                }
            }
        }
    
    private external fun nativeCreate(userId: String): Long
    private external fun nativeDestroy(handle: Long)
    private external fun nativeValidateEmail(
        handle: Long,
        email: String
    ): EmailValidation
    private external fun nativeFetchProfileAsync(
        handle: Long,
        callback: (String) -> Unit
    )
    
    companion object {
        init {
            System.loadLibrary("shared_core")
        }
    }
}
```

The JNI implementation bridges between the C API and Java method signatures, managing string conversions and object creation:

```cpp
// jni_bridge.cpp
#include <jni.h>
#include "shared_core.h"
#include <string>
#include <pthread.h>

// Global JVM reference for callback thread attachment
static JavaVM* g_jvm = nullptr;

JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    g_jvm = vm;
    return JNI_VERSION_1_6;
}

extern "C" JNIEXPORT jlong JNICALL
Java_com_example_shared_UserSession_nativeCreate(
    JNIEnv* env,
    jobject obj,
    jstring userId
) {
    const char* userIdCStr = env->GetStringUTFChars(userId, nullptr);
    UserSession* session = user_session_create(userIdCStr);
    env->ReleaseStringUTFChars(userId, userIdCStr);
    
    return reinterpret_cast<jlong>(session);
}

extern "C" JNIEXPORT void JNICALL
Java_com_example_shared_UserSession_nativeDestroy(
    JNIEnv* env,
    jobject obj,
    jlong handle
) {
    UserSession* session = reinterpret_cast<UserSession*>(handle);
    user_session_destroy(session);
}

extern "C" JNIEXPORT jobject JNICALL
Java_com_example_shared_UserSession_nativeValidateEmail(
    JNIEnv* env,
    jobject obj,
    jlong handle,
    jstring email
) {
    UserSession* session = reinterpret_cast<UserSession*>(handle);
    const char* emailCStr = env->GetStringUTFChars(email, nullptr);
    
    ValidationResult* result = user_session_validate_email(
        session,
        emailCStr
    );
    env->ReleaseStringUTFChars(email, emailCStr);
    
    bool isValid = validation_result_is_valid(result);
    const char* errorCStr = validation_result_get_error(result);
    jstring errorMsg = errorCStr ? 
        env->NewStringUTF(errorCStr) : nullptr;
    
    validation_result_destroy(result);
    
    // Create EmailValidation object
    jclass validationClass = env->FindClass(
        "com/example/shared/UserSession$EmailValidation"
    );
    jmethodID constructor = env->GetMethodID(
        validationClass,
        "<init>",
        "(ZLjava/lang/String;)V"
    );
    
    return env->NewObject(
        validationClass,
        constructor,
        isValid,
        errorMsg
    );
}

// Callback wrapper for async operations
struct JNICallbackContext {
    jobject callback_obj;  // GlobalRef to Kotlin lambda
};

void jni_async_callback(void* context, const char* result) {
    JNICallbackContext* ctx = 
        static_cast<JNICallbackContext*>(context);
    
    // Attach current thread to JVM
    JNIEnv* env;
    bool needDetach = false;
    
    int getEnvStatus = g_jvm->GetEnv(
        reinterpret_cast<void**>(&env),
        JNI_VERSION_1_6
    );
    
    if (getEnvStatus == JNI_EDETACHED) {
        if (g_jvm->AttachCurrentThread(&env, nullptr) == 0) {
            needDetach = true;
        } else {
            return;  // Failed to attach
        }
    }
    
    // Invoke Kotlin callback: (String) -> Unit
    jclass functionClass = env->FindClass("kotlin/jvm/functions/Function1");
    jmethodID invokeMethod = env->GetMethodID(
        functionClass,
        "invoke",
        "(Ljava/lang/Object;)Ljava/lang/Object;"
    );
    
    jstring resultStr = env->NewStringUTF(result);
    env->CallObjectMethod(ctx->callback_obj, invokeMethod, resultStr);
    
    // Cleanup
    env->DeleteGlobalRef(ctx->callback_obj);
    delete ctx;
    
    if (needDetach) {
        g_jvm->DetachCurrentThread();
    }
}

extern "C" JNIEXPORT void JNICALL
Java_com_example_shared_UserSession_nativeFetchProfileAsync(
    JNIEnv* env,
    jobject obj,
    jlong handle,
    jobject callback
) {
    UserSession* session = reinterpret_cast<UserSession*>(handle);
    
    // Create global reference for callback (survives thread transition)
    JNICallbackContext* context = new JNICallbackContext{
        env->NewGlobalRef(callback)
    };
    
    user_session_fetch_profile_async(
        session,
        jni_async_callback,
        context
    );
}
```

The build system unification for native modules typically uses CMake to compile the shared C/C++ code for both platforms. The CMakeLists file defines a single library target that both iOS and Android build systems invoke:

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.18)
project(shared_core)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Shared library sources
add_library(shared_core SHARED
    shared_core.cpp
)

# Platform-specific JNI bridge for Android
if(ANDROID)
    target_sources(shared_core PRIVATE jni_bridge.cpp)
    target_link_libraries(shared_core log)
endif()

# iOS framework configuration
if(IOS)
    set_target_properties(shared_core PROPERTIES
        FRAMEWORK TRUE
        MACOSX_FRAMEWORK_IDENTIFIER com.example.sharedcore
        MACOSX_FRAMEWORK_INFO_PLIST ${CMAKE_CURRENT_SOURCE_DIR}/Info.plist
        PUBLIC_HEADER shared_core.h
    )
endif()

# Compiler flags for performance
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(shared_core PRIVATE
        -O3
        -flto
        -fvisibility=hidden
    )
    
    if(NOT ANDROID)
        # Link-time optimization
        set_target_properties(shared_core PROPERTIES
            INTERPROCEDURAL_OPTIMIZATION TRUE
        )
    endif()
endif()
```

The Android project integrates CMake through the Gradle plugin, specifying the native library path and ABI targets:

```kotlin
// app/build.gradle.kts
android {
    compileSdk = 34
    
    defaultConfig {
        minSdk = 24
        targetSdk = 34
        
        externalNativeBuild {
            cmake {
                cppFlags += "-std=c++17"
                abiFilters += listOf("arm64-v8a", "armeabi-v7a")
            }
        }
    }
    
    externalNativeBuild {
        cmake {
            path = file("../../shared/CMakeLists.txt")
            version = "3.22.1"
        }
    }
    
    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

The iOS project adds the CMake framework as a build phase, invoking CMake during Xcode's build process through a Run Script phase:

```bash
#!/bin/bash
# Xcode Run Script Build Phase

set -e

SHARED_DIR="${SRCROOT}/../../shared"
BUILD_DIR="${DERIVED_FILE_DIR}/cmake_build"
FRAMEWORK_NAME="shared_core.framework"

# Determine architecture
if [ "${PLATFORM_NAME}" = "iphonesimulator" ]; then
    ARCHS="x86_64;arm64"
    SDK="iphonesimulator"
else
    ARCHS="arm64"
    SDK="iphoneos"
fi

# Configure CMake
cmake -B "${BUILD_DIR}" \
    -G Xcode \
    -DCMAKE_SYSTEM_NAME=iOS \
    -DCMAKE_OSX_ARCHITECTURES="${ARCHS}" \
    -DCMAKE_OSX_SYSROOT="${SDK}" \
    -DCMAKE_BUILD_TYPE="${CONFIGURATION}" \
    -DIOS=ON \
    "${SHARED_DIR}"

# Build framework
cmake --build "${BUILD_DIR}" --config "${CONFIGURATION}"

# Copy to products directory
cp -R "${BUILD_DIR}/${CONFIGURATION}-${SDK}/${FRAMEWORK_NAME}" \
    "${TARGET_BUILD_DIR}/${FRAMEWORKS_FOLDER_PATH}/"
```

JavaScript bridge architectures like React Native shift the cross-platform boundary higher in the stack, executing shared business logic in a JavaScript VM while delegating platform-specific operations to native modules through asynchronous message passing. The architecture comprises three components: the JavaScript runtime (typically JavaScriptCore on iOS, Hermes on Android), the native bridge that serializes messages between JavaScript and native code, and the native module implementations that expose platform APIs to JavaScript.

The bridge communication mechanism fundamentally constrains performance characteristics. All data crossing the bridge must serialize to JSON, introducing allocation overhead and preventing zero-copy data sharing. Method calls from JavaScript to native code enqueue messages on a background thread, introducing unpredictable latency from queue depth and thread scheduling. Return values require another bridge crossing in the opposite direction, doubling the serialization cost for synchronous-style APIs. These constraints make React Native architectures unsuitable for high-frequency, low-latency operations like audio processing, real-time sensor fusion, or computational geometry, but acceptable for business logic that operates on coarse-grained data structures with relaxed timing requirements.

The native module interface on iOS uses Objective-C runtime introspection to expose native methods to JavaScript. Modules declare themselves through RCT_EXPORT_MODULE and annotate methods with RCT_EXPORT_METHOD, allowing the bridge to construct a method registry at runtime:

```objc
// RNUserSession.m
#import <React/RCTBridgeModule.h>
#import <React/RCTEventEmitter.h>

@interface RNUserSession : RCTEventEmitter <RCTBridgeModule>
@end

@implementation RNUserSession {
    NSString* _userId;
}

RCT_EXPORT_MODULE(UserSession);

+ (BOOL)requiresMainQueueSetup {
    return NO;  // Initialize on background thread
}

- (NSArray<NSString *> *)supportedEvents {
    return @[@"onProfileUpdate"];
}

RCT_EXPORT_METHOD(initialize:(NSString *)userId
                  resolver:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject) {
    _userId = userId;
    resolve(@{@"success": @YES});
}

RCT_EXPORT_METHOD(validateEmail:(NSString *)email
                  resolver:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject) {
    NSString* pattern = 
        @"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$";
    NSPredicate* predicate = 
        [NSPredicate predicateWithFormat:@"SELF MATCHES %@", pattern];
    
    BOOL isValid = [predicate evaluateWithObject:email];
    
    resolve(@{
        @"isValid": @(isValid),
        @"errorMessage": isValid ? [NSNull null] : @"Invalid format"
    });
}

RCT_EXPORT_METHOD(fetchProfile:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject) {
    dispatch_async(dispatch_get_global_queue(
        DISPATCH_QUEUE_PRIORITY_DEFAULT, 0
    ), ^{
        // Simulate network request
        [NSThread sleepForTimeInterval:0.1];
        
        NSDictionary* profile = @{
            @"name": @"User",
            @"id": self->_userId
        };
        
        dispatch_async(dispatch_get_main_queue(), ^{
            resolve(profile);
            [self sendEventWithName:@"onProfileUpdate" body:profile];
        });
    });
}

@end
```

The Android native module uses similar annotations with a Java-based module system:

```java
// UserSessionModule.java
package com.example.modules;

import com.facebook.react.bridge.ReactApplicationContext;
import com.facebook.react.bridge.ReactContextBaseJavaModule;
import com.facebook.react.bridge.ReactMethod;
import com.facebook.react.bridge.Promise;
import com.facebook.react.bridge.WritableMap;
import com.facebook.react.bridge.Arguments;
import com.facebook.react.modules.core.DeviceEventManagerModule;

import java.util.regex.Pattern;
import java.util.regex.Matcher;

public class UserSessionModule extends ReactContextBaseJavaModule {
    private static final String MODULE_NAME = "UserSession";
    private String userId;
    
    public UserSessionModule(ReactApplicationContext context) {
        super(context);
    }
    
    @Override
    public String getName() {
        return MODULE_NAME;
    }
    
    @ReactMethod
    public void initialize(String userId, Promise promise) {
        this.userId = userId;
        
        WritableMap result = Arguments.createMap();
        result.putBoolean("success", true);
        promise.resolve(result);
    }
    
    @ReactMethod
    public void validateEmail(String email, Promise promise) {
        Pattern pattern = Pattern.compile(
            "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        );
        Matcher matcher = pattern.matcher(email);
        boolean isValid = matcher.matches();
        
        WritableMap result = Arguments.createMap();
        result.putBoolean("isValid", isValid);
        if (!isValid) {
            result.putString("errorMessage", "Invalid format");
        }
        
        promise.resolve(result);
    }
    
    @ReactMethod
    public void fetchProfile(final Promise promise) {
        new Thread(() -> {
            try {
                Thread.sleep(100);
                
                WritableMap profile = Arguments.createMap();
                profile.putString("name", "User");
                profile.putString("id", userId);
                
                promise.resolve(profile);
                
                // Emit event
                getReactApplicationContext()
                    .getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter.class)
                    .emit("onProfileUpdate", profile);
                    
            } catch (InterruptedException e) {
                promise.reject("ERROR", e);
            }
        }).start();
    }
}
```

The JavaScript layer wraps the native modules in a type-safe interface, providing async/await syntax over the promise-based bridge:

```typescript
// UserSession.ts
import { NativeModules, NativeEventEmitter } from 'react-native';

const { UserSession: NativeUserSession } = NativeModules;

interface EmailValidation {
  isValid: boolean;
  errorMessage?: string;
}

interface UserProfile {
  name: string;
  id: string;
}

class UserSession {
  private eventEmitter = new NativeEventEmitter(NativeUserSession);
  private profileListeners: ((profile: UserProfile) => void)[] = [];
  
  constructor(userId: string) {
    NativeUserSession.initialize(userId);
    
    this.eventEmitter.addListener(
      'onProfileUpdate',
      (profile: UserProfile) => {
        this.profileListeners.forEach(listener => listener(profile));
      }
    );
  }
  
  async validateEmail(email: string): Promise<EmailValidation> {
    return await NativeUserSession.validateEmail(email);
  }
  
  async fetchProfile(): Promise<UserProfile> {
    return await NativeUserSession.fetchProfile();
  }
  
  onProfileUpdate(listener: (profile: UserProfile) => void): () => void {
    this.profileListeners.push(listener);
    return () => {
      const index = this.profileListeners.indexOf(listener);
      if (index >= 0) {
        this.profileListeners.splice(index, 1);
      }
    };
  }
}

export default UserSession;
```

Ahead-of-time compilation frameworks like Flutter avoid bridge serialization by compiling a single language (Dart) to native ARM64 code for both platforms. Flutter's architecture renders UI through Skia (a 2D graphics engine) rather than platform-native widgets, providing pixel-perfect consistency across platforms but losing platform-specific UI conventions. The Dart VM executes during development for hot-reload, while release builds compile Dart code ahead-of-time to native machine code using LLVM.

Flutter's platform channel mechanism provides bidirectional communication between Dart and native code for accessing platform APIs not exposed through Flutter's framework. Channels use binary message codecs (typically StandardMessageCodec or JSONMessageCodec) to serialize method calls and return values:

```dart
// user_session.dart
import 'package:flutter/services.dart';

class UserSession {
  static const _channel = MethodChannel('com.example/user_session');
  
  final String userId;
  
  UserSession(this.userId) {
    _channel.invokeMethod('initialize', {'userId': userId});
  }
  
  Future<EmailValidation> validateEmail(String email) async {
    final result = await _channel.invokeMethod<Map>(
      'validateEmail',
      {'email': email}
    );
    
    return EmailValidation(
      isValid: result!['isValid'] as bool,
      errorMessage: result['errorMessage'] as String?,
    );
  }
  
  Future<Map<String, dynamic>> fetchProfile() async {
    final profile = await _channel.invokeMethod<Map>(
      'fetchProfile'
    );
    return Map<String, dynamic>.from(profile!);
  }
  
  Stream<Map<String, dynamic>> get profileUpdates {
    return EventChannel('com.example/profile_updates')
        .receiveBroadcastStream()
        .map((event) => Map<String, dynamic>.from(event as Map));
  }
}

class EmailValidation {
  final bool isValid;
  final String? errorMessage;
  
  EmailValidation({required this.isValid, this.errorMessage});
}
```

The iOS platform channel handler implements the native side:

```swift
// UserSessionPlugin.swift
import Flutter

class UserSessionPlugin: NSObject, FlutterPlugin {
    private var userId: String?
    private var eventSink: FlutterEventSink?
    
    static func register(with registrar: FlutterPluginRegistrar) {
        let channel = FlutterMethodChannel(
            name: "com.example/user_session",
            binaryMessenger: registrar.messenger()
        )
        
        let eventChannel = FlutterEventChannel(
            name: "com.example/profile_updates",
            binaryMessenger: registrar.messenger()
        )
        
        let instance = UserSessionPlugin()
        registrar.addMethodCallDelegate(instance, channel: channel)
        eventChannel.setStreamHandler(instance)
    }
    
    func handle(
        _ call: FlutterMethodCall,
        result: @escaping FlutterResult
    ) {
        switch call.method {
        case "initialize":
            guard let args = call.arguments as? [String: Any],
                  let userId = args["userId"] as? String else {
                result(FlutterError(
                    code: "INVALID_ARGS",
                    message: "Missing userId",
                    details: nil
                ))
                return
            }
            self.userId = userId
            result(["success": true])
            
        case "validateEmail":
            guard let args = call.arguments as? [String: Any],
                  let email = args["email"] as? String else {
                result(FlutterError(
                    code: "INVALID_ARGS",
                    message: "Missing email",
                    details: nil
                ))
                return
            }
            
            let pattern = 
                "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
            let predicate = NSPredicate(
                format: "SELF MATCHES %@",
                pattern
            )
            let isValid = predicate.evaluate(with: email)
            
            result([
                "isValid": isValid,
                "errorMessage": isValid ? NSNull() : "Invalid format"
            ])
            
        case "fetchProfile":
            DispatchQueue.global().async {
                Thread.sleep(forTimeInterval: 0.1)
                
                let profile: [String: Any] = [
                    "name": "User",
                    "id": self.userId ?? ""
                ]
                
                DispatchQueue.main.async {
                    result(profile)
                    self.eventSink?(profile)
                }
            }
            
        default:
            result(FlutterMethodNotImplemented)
        }
    }
}

extension UserSessionPlugin: FlutterStreamHandler {
    func onListen(
        withArguments arguments: Any?,
        eventSink events: @escaping FlutterEventSink
    ) -> FlutterError? {
        self.eventSink = events
        return nil
    }
    
    func onCancel(withArguments arguments: Any?) -> FlutterError? {
        self.eventSink = nil
        return nil
    }
}
```

Kotlin Multiplatform Mobile (KMM) represents a fundamentally different approach by compiling Kotlin code to multiple native targets: JVM bytecode for Android, native binaries through Kotlin/Native's LLVM backend for iOS. KMM allows gradual adoption—shared business logic lives in a common module while platform-specific code remains in platform-specific modules, both written in Kotlin. The architecture uses expect/actual declarations to define platform-specific interfaces in common code and provide concrete implementations in each platform module.

The common module defines the shared business logic and declares expected platform dependencies:

```kotlin
// commonMain/UserSession.kt
package com.example.shared

expect class PlatformContext

expect fun currentTimeMillis(): Long

expect suspend fun httpGet(url: String): String

class UserSession(private val userId: String) {
    private val emailPattern = Regex(
        "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}\$"
    )
    
    data class EmailValidation(
        val isValid: Boolean,
        val errorMessage: String?
    )
    
    fun validateEmail(email: String): EmailValidation {
        val isValid = emailPattern.matches(email)
        return EmailValidation(
            isValid = isValid,
            errorMessage = if (isValid) null else "Invalid format"
        )
    }
    
    suspend fun fetchProfile(): Map<String, String> {
        // Simulate network delay
        kotlinx.coroutines.delay(100)
        
        return mapOf(
            "name" to "User",
            "id" to userId,
            "timestamp" to currentTimeMillis().toString()
        )
    }
}
```

The Android actual implementation provides JVM-specific platform bindings:

```kotlin
// androidMain/UserSession.kt
package com.example.shared

import android.content.Context

actual typealias PlatformContext = Context

actual fun currentTimeMillis(): Long = System.currentTimeMillis()

actual suspend fun httpGet(url: String): String {
    return kotlinx.coroutines.withContext(
        kotlinx.coroutines.Dispatchers.IO
    ) {
        java.net.URL(url).readText()
    }
}
```

The iOS actual implementation uses Kotlin/Native bindings to Foundation APIs:

```kotlin
// iosMain/UserSession.kt
package com.example.shared

import platform.Foundation.NSDate
import platform.Foundation.timeIntervalSince1970
import platform.Foundation.NSURL
import platform.Foundation.NSURLSession
import platform.Foundation.NSURLRequest
import platform.Foundation.NSURLResponse
import platform.Foundation.NSData
import platform.Foundation.NSString
import platform.Foundation.NSUTF8StringEncoding
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlin.coroutines.suspendCoroutine

actual class PlatformContext

actual fun currentTimeMillis(): Long {
    return (NSDate().timeIntervalSince1970 * 1000).toLong()
}

actual suspend fun httpGet(url: String): String = 
    suspendCoroutine { continuation ->
        val nsUrl = NSURL(string = url)
        val request = NSURLRequest(uRL = nsUrl)
        
        NSURLSession.sharedSession.dataTaskWithRequest(request) { 
            data, response, error ->
            
            if (error != null) {
                continuation.resumeWithException(
                    Exception(error.localizedDescription)
                )
                return@dataTaskWithRequest
            }
            
            val responseData = data ?: run {
                continuation.resumeWithException(
                    Exception("No data received")
                )
                return@dataTaskWithRequest
            }
            
            val text = NSString.create(
                data = responseData,
                encoding = NSUTF8StringEncoding
            ) as String
            
            continuation.resume(text)
        }.resume()
    }
```

The build configuration uses Gradle with Kotlin Multiplatform plugin to coordinate compilation across targets:

```kotlin
// shared/build.gradle.kts
plugins {
    kotlin("multiplatform")
    id("com.android.library")
}

kotlin {
    android {
        compilations.all {
            kotlinOptions {
                jvmTarget = "11"
            }
        }
    }
    
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "shared"
            isStatic = true
        }
    }
    
    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
            }
        }
        
        val androidMain by getting {
            dependencies {
                implementation("androidx.core:core-ktx:1.12.0")
            }
        }
        
        val iosX64Main by getting
        val iosArm64Main by getting
        val iosSimulatorArm64Main by getting
        val iosMain by creating {
            dependsOn(commonMain)
            iosX64Main.dependsOn(this)
            iosArm64Main.dependsOn(this)
            iosSimulatorArm64Main.dependsOn(this)
        }
    }
}

android {
    namespace = "com.example.shared"
    compileSdk = 34
    defaultConfig {
        minSdk = 24
    }
}
```

The iOS project imports the generated framework and uses it from Swift:

```swift
// ContentView.swift
import SwiftUI
import shared

struct ContentView: View {
    @State private var email = ""
    @State private var validationResult: String = ""
    @State private var profile: [String: String]?
    
    private let session = UserSession(userId: "user123")
    
    var body: some View {
        VStack(spacing: 20) {
            TextField("Email", text: $email)
                .textFieldStyle(.roundedBorder)
                .autocapitalization(.none)
            
            Button("Validate") {
                let result = session.validateEmail(email: email)
                validationResult = result.isValid 
                    ? "Valid" 
                    : result.errorMessage ?? "Invalid"
            }
            
            Text(validationResult)
            
            Button("Fetch Profile") {
                Task {
                    do {
                        let profileData = try await session.fetchProfile()
                        // Convert KotlinX Map to Swift Dictionary
                        var dict: [String: String] = [:]
                        for key in profileData.keys {
                            if let value = profileData[key] as? String {
                                dict[key as! String] = value
                            }
                        }
                        profile = dict
                    } catch {
                        print("Error: \(error)")
                    }
                }
            }
            
            if let profile = profile {
                VStack(alignment: .leading) {
                    Text("Name: \(profile["name"] ?? "")")
                    Text("ID: \(profile["id"] ?? "")")
                    Text("Timestamp: \(profile["timestamp"] ?? "")")
                }
            }
        }
        .padding()
    }
}
```

## 3. High-Performance Optimization & Failure Modes

Cross-platform architecture performance optimization begins with minimizing bridge crossings and serialization overhead. Every transition between shared code and platform-specific code incurs measurable cost—JNI calls on Android consume 100-200 nanoseconds per invocation, React Native bridge messages add 1-2 milliseconds of latency including queue delays, and even Kotlin/Native's C interop requires pointer dereferencing and calling convention translation. Performance-critical paths must batch operations to amortize crossing costs across multiple data items rather than making repeated fine-grained calls.

The canonical optimization pattern moves computation into the shared core rather than orchestrating it from platform-specific code through repeated bridge calls. Consider a data validation pipeline that checks multiple fields: a naive implementation would call individual validation functions for each field from Swift or Kotlin, incurring one bridge crossing per field. The optimized implementation passes the entire data structure to the shared core once, performs all validations in a tight loop, and returns a composite result, reducing N bridge crossings to one. The performance difference becomes dramatic for collections—validating 100 email addresses through 100 individual bridge calls versus one batched call that processes the array in the shared core.

Memory management failures dominate cross-platform architecture defects. The iOS bridge must retain C objects for the lifetime of their Swift wrappers, but premature deallocation creates dangling pointers that manifest as EXC_BAD_ACCESS crashes when Swift code attempts to use the destroyed native object. The solution requires careful lifetime tracking through strong references or explicitly incrementing reference counts in the C layer when creating objects that Swift will own. The inverse failure occurs when Swift objects passed to C callbacks outlive their expected scope—the C layer must not cache pointers to Swift objects without explicitly retaining them through bridging casts.

Android's JNI introduces different lifetime hazards. Local JNI references automatically deallocate when the native method returns, creating dangling pointers if the C++ code attempts to cache jobject pointers for later use. All cached Java objects must convert to global references through NewGlobalRef, with explicit DeleteGlobalRef calls when the reference is no longer needed. Failure to delete global references creates memory leaks that Android's garbage collector cannot reclaim. The threading constraint compounds this—JNIEnv pointers are thread-local and cannot be cached or passed to other threads. Background threads must call AttachCurrentThread before making any JNI calls, and must call DetachCurrentThread before thread termination to prevent resource leaks.

Threading model mismatches create subtle race conditions and deadlocks. Platform UI frameworks enforce main-thread access for all UI operations—UIKit on iOS crashes if view properties are modified from background threads, and Android throws CalledFromWrongThreadException. Shared core logic that performs background computation must carefully marshal completion callbacks back to the main thread. The bridge layer typically provides dispatch mechanisms (DispatchQueue.main.async on iOS, Handler(Looper.getMainLooper()).post on Android), but incorrect usage creates race conditions when multiple threads simultaneously update shared state.

The callback threading failure mode manifests when native code invokes a callback on a background thread without considering platform threading requirements. A C++ async operation might call a Swift closure from a worker thread, but if that closure updates UI, the app crashes. The correct pattern requires the bridge layer to capture the original calling thread's dispatch context and explicitly dispatch the callback back to that thread. React Native handles this automatically by always invoking JavaScript callbacks on the JavaScript thread, but raw JNI and Swift bridges require manual dispatch handling.

String encoding failures occur at every text boundary crossing. iOS and Android both use UTF-16 internally for string representation (NSString and java.lang.String), while C APIs typically use UTF-8 null-terminated char arrays. The conversion APIs (GetStringUTFChars, utf8CString) handle the common cases, but fail silently on invalid UTF-8 sequences or produce incorrect results when the C code assumes ASCII. Emoji and non-Latin scripts expose these failures—a string containing emoji may consume different byte counts in UTF-8 and UTF-16, breaking length calculations if the code assumes one-byte-per-character. The defensive pattern validates UTF-8 on all incoming strings and uses explicit length parameters rather than relying on null termination.

Build system integration failures typically manifest as missing symbols or ABI incompatibilities at link time. The iOS build might successfully compile shared C++ code but fail to link if the CMake target uses different C++ standard library settings than Xcode's default (libc++ vs libstdc++). Android's NDK provides multiple API levels with different symbol availability—code that links against API level 29 functions will crash at runtime on API level 24 devices. The mitigation requires explicit __builtin_available checks on iOS and dlopen/dlsym dynamic loading on Android for symbols not guaranteed available at the minimum deployment target.

Code signing and entitlements create iOS-specific failure modes. Dynamic frameworks embedded in the app bundle must be signed with the same certificate as the app, and must include appropriate entitlements for features they use. A shared framework that accesses the keychain requires the keychain-access-groups entitlement, and attempting to use it without proper entitlements causes silent keychain operation failures. The Xcode build process should automatically re-sign embedded frameworks, but manual CMake-generated frameworks may skip this step, causing App Store rejection or runtime security errors.

Dependency versioning conflicts emerge when the shared core depends on libraries that conflict with platform framework versions. If the shared C++ code links against OpenSSL 1.1 but iOS already includes OpenSSL 3.0 in its system libraries, symbol collisions cause crashes. The solution requires either static linking with symbol hiding (using visibility attributes and linker version scripts) or namespace mangling to prevent symbol collisions. Rust's approach of prefixing all symbols with crate names provides automatic collision avoidance, making Rust an attractive choice for shared mobile logic despite the FFI complexity.

Hot-reload and development iteration speed suffer in native-shared architectures. React Native and Flutter provide near-instant code updates during development through hot-reload mechanisms that patch the running app with code changes. Native module architectures require full app recompilation and reinstallation for every change to the shared C/C++/Rust code, imposing 30-60 second iteration cycles. The productivity impact pushes teams toward JavaScript bridge architectures for rapid prototyping, accepting the bridge overhead in exchange for development velocity. Some projects compromise by prototyping in React Native and later rewriting performance-critical paths as native modules once the architecture stabilizes.

Testing cross-platform shared code requires running identical test suites on both platforms to catch platform-specific failures. A validation function might pass tests on iOS but fail on Android due to different regular expression engine behavior or different floating-point rounding. The test strategy must include both unit tests that run in isolation against the shared core (linked as a plain dynamic library in a test harness) and integration tests that exercise the full bridge layer on each platform. Continuous integration pipelines must build and test for both platforms on every commit, catching incompatibilities before they reach production.

Debugging native crashes in cross-platform code requires platform-specific tools. iOS crashes produce crash reports with symbolicated stack traces if the dSYM files are available, but C++ symbols require manual demangling with c++filt. Android native crashes write tombstones to logcat with partial stack traces, but full symbolication requires addr2line against the unstripped native library. Both platforms support attaching debuggers (lldb on iOS, gdb or lldb on Android through adb), but breakpoints in shared code must account for compiler optimizations that inline functions or reorder instructions.

The optimization strategy depends critically on profiling the actual bridge overhead for the specific workload. Many projects prematurely optimize by moving all logic to native code, but real-world measurements often show that bridge costs are negligible compared to network latency, JSON parsing, or UI rendering time. The productive approach profiles first, identifies the actual bottleneck, and applies targeted optimization only to confirmed hot paths. A validation function called once per form submission tolerates millisecond-scale bridge latency, while a real-time audio synthesizer demands native implementation with zero bridge crossings in the critical path.
