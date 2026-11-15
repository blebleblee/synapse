# Lesson 3: Gameplay Framework, Actor Lifecycle, Component Architecture

## 1. First-Principles Intuition & Invariants

Unreal Engine's gameplay framework is a garbage-collected object system layered on top of a native C++ memory model, and understanding it requires confronting a fundamental tension: game objects demand deterministic destruction and frame-precise lifecycle transitions, but the engine's memory substrate is a tracing garbage collector that defers finalization. The `UObject` base class is the root of this hierarchy, and every gameplay-relevant entity—actors, components, subsystems—participates in the same `UObject`-derived reflection system that drives serialization, replication, metadata queries, and GC root scanning. An `AActor` is not merely an object; it is a `UObject` that has been inserted into a `UWorld`, granted a transform in identity in the spatial index, and registered with the engine's ticking infrastructure. The act of spawning an actor is a multi-phase transaction: memory allocation, `UObject` initialization, component registration, location/rotation resolution, and a final `BeginPlay` notification that flips the actor from a dormant constructed state into a per-frame active participant.

The critical invariant every systems programmer must internalize is that `AActor` instances are never destroyed synchronously. When you call `Destroy()` on an actor, you are not deallocating memory. You are registering the actor with the garbage collector for deferred collection, setting its `IsPendingKill` flag to true, removing it from the tick list, detaching its components from the scene, and queuing its removal from the owning `ULevel`. The actual memory is reclaimed later, on the next GC pass, which runs on a separate thread and scans the UObject reference graph for live roots. This means any raw `UObject*` pointer you hold can become a dangling pointer to memory that is still mapped but semantically dead. The engine provides `TWeakObjectPtr<T>` as a safe access primitive—a weak reference that returns null when the object is pending kill or has been collected—and every external reference to an actor you do not own should use this type. A raw `AActor*` is safe only within the scope where you can guarantee the actor's lifetime, typically inside member functions of the actor itself or its owned components.

The Actor-Component architecture is a composition-based design where the actor serves as a coordinate frame and a container, while components are the behavioral and data units. This separation mirrors the entity-component-system pattern but with a critical distinction: Unreal components are themselves `UObject`s, they participate in garbage collection, and they have their own lifecycle with `BeginPlay`, `TickComponent`, `EndPlay`, and `OnComponentDestroyed` callbacks. A `USceneComponent` derives from `UActorComponent` and adds a transform—a relative location, rotation, and scale—plus an attachment graph that links it to a parent component. This attachment graph is the spine of the actor's spatial representation. When an actor moves, it moves its root component, and the root component propagates that transform down to its attached children. The `UPrimitiveComponent` layer adds rendering meshes, collision geometry, and physics body integration on top of the scene component's transform. Understanding this chain—`UActorComponent` to `USceneComponent` to `UPrimitiveComponent`—is essential because each layer introduces new lifecycle hooks, new failure modes, and new performance costs.

World partitioning and level streaming are the engine's answers to the problem of scene scale. A single `UWorld` can contain hundreds of megabytes of geometry and thousands of actors, and attempting to hold all of that in memory simultaneously is infeasible for large open-world games. The traditional solution was `ULevelStreaming`, which loads and unloads entire sublevels as units, swapping their actor sets in and out of the world. The modern solution, introduced in Unreal Engine 5, is `UWorldPartition`, which replaces discrete sublevels with a continuous spatial grid. The world is divided into cells, and each cell contains a set of streaming sources—points in space that determine which cells should be loaded. As the player moves through the world, the streaming system loads cells ahead of the player and unloads cells behind them, all on background threads, while the game thread continues to run. This is fundamentally a memory paging system, and like any paging system, its performance is determined by the working set size, the cell granularity, and the streaming source's predictive lookahead.

## 2. Core Architecture & Mechanics

The actor spawning pipeline is the most important lifecycle transaction in the engine, and it proceeds through a deterministic sequence of internal calls. When you invoke `UWorld::SpawnActor`, the engine constructs the actor by calling `StaticConstructObject_Internal`, which allocates memory, zero-initializes the object, runs the C++ constructor, and registers the object with the `UObject` hash tables for future lookup. After construction, the engine calls `AActor::PostActorCreated`, which is the first hook where the actor can perform initialization that depends on its `UWorld` context being available. The engine then processes the spawn parameters: if `bDeferConstruction` is true, the actor's `OnConstruction` script hook is deferred until the transform is finalized; otherwise, it runs immediately. Component registration follows, where each component that was marked as `bAutoRegister` in its constructor is added to the actor's `OwnedComponents` set and, for scene components, inserted into the scene's transform hierarchy. The final step is `AActor::BeginPlay`, which is dispatched by the world's gameplay ticker after the actor is fully registered. `BeginPlay` propagates to all components via `AActor::DispatchBeginPlay`, which calls `UActorComponent::BeginPlay` on each component in the actor's component set.

The C++ code below demonstrates a complete, compilable actor class that exercises every stage of this lifecycle. It declares a custom scene component as a root, attaches a static mesh component as a child, overrides `PostActorCreated` and `BeginPlay` and `EndPlay` and `Destroyed`, and logs each phase so you can observe the exact ordering in the output log.

```cpp
// LifecycleDemoActor.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LifecycleDemoActor.generated.h"

UCLASS(BlueprintType, Blueprintable, Category = "Lesson3")
class ALifecycleDemoActor : public AActor
{
    GENERATED_BODY()

public:
    ALifecycleDemoActor();

    // Called after the actor is spawned via SpawnActor (not loaded from disk).
    virtual void PostActorCreated() override;

    // Called after the actor is serialized from disk (load or duplication).
    virtual void PostLoad() override;

    // Called when the actor is placed in the level editor.
    virtual void OnConstruction(const FTransform& Transform) override;

    // Lifecycle entry/exit points.
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void Destroyed() override;

    // Per-frame tick.
    virtual void Tick(float DeltaTime) override;

    // Blueprint-callable factory that demonstrates manual spawning.
    UFUNCTION(BlueprintCallable, Category = "Lesson3", meta = (WorldContext = "WorldContextObject"))
    static ALifecycleDemoActor* SpawnInWorld(UObject* WorldContextObject, FVector Location, FRotator Rotation);

protected:
    // Root component: a SceneComponent that anchors the actor in space.
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Lesson3")
    USceneComponent* RootSceneComponent;

    // Child component: a StaticMeshComponent attached to the root.
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Lesson3")
    UStaticMeshComponent* MeshComponent;

private:
    // A weak reference we store to demonstrate safe pointer patterns.
    TWeakObjectPtr<AActor> WeakSelfReference;
};
```

```cpp
// LifecycleDemoActor.cpp
#include "LifecycleDemoActor.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

ALifecycleDemoActor::ALifecycleDemoActor()
{
    // Enable ticking and set the tick group. PrePhysics means this actor ticks
    // before the physics simulation step runs for this frame.
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
    PrimaryActorTick.TickGroup = TG_PrePhysics;

    // Create the root scene component and set it as the actor's root.
    RootSceneComponent = CreateDefaultSubobject<USceneComponent>(TEXT("RootSceneComponent"));
    RootSceneComponent->SetupAttachment(RootComponent);
    SetRootComponent(RootSceneComponent);

    // Create the mesh component and attach it to the root.
    // CreateDefaultSubobject guarantees the component is owned by this actor's
    // subobject archetype, so it serializes and replicates correctly.
    MeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MeshComponent"));
    MeshComponent->SetupAttachment(RootSceneComponent);

    // Load a default cube mesh from the engine content so the actor is visible.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMeshFinder(
        TEXT("/Engine/BasicShapes/Cube"));
    if (CubeMeshFinder.Succeeded())
    {
        MeshComponent->SetStaticMesh(CubeMeshFinder.Object);
    }

    // Set a reasonable default scale.
    MeshComponent->SetWorldScale3D(FVector(0.5f));
}

void ALifecycleDemoActor::PostActorCreated()
{
    Super::PostActorCreated();
    UE_LOG(LogTemp, Log, TEXT("LifecycleDemoActor [%s]: PostActorCreated"), *GetName());
}

void ALifecycleDemoActor::PostLoad()
{
    Super::PostLoad();
    UE_LOG(LogTemp, Log, TEXT("LifecycleDemoActor [%s]: PostLoad"), *GetName());
}

void ALifecycleDemoActor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    UE_LOG(LogTemp, Log, TEXT("LifecycleDemoActor [%s]: OnConstruction at %s"),
        *GetName(), *Transform.ToHumanReadableString());
}

void ALifecycleDemoActor::BeginPlay()
{
    Super::BeginPlay();
    UE_LOG(LogTemp, Log, TEXT("LifecycleDemoActor [%s]: BeginPlay"), *GetName());

    // Store a weak pointer to ourselves to demonstrate safe self-reference.
    WeakSelfReference = this;

    // Verify the component hierarchy is correctly set up.
    if (RootComponent != nullptr)
    {
        UE_LOG(LogTemp, Log, TEXT("LifecycleDemoActor [%s]: Root = %s, Attach count = %d"),
            *GetName(),
            *RootComponent->GetName(),
            RootComponent->GetAttachChildren().Num());
    }
}

void ALifecycleDemoActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    UE_LOG(LogTemp, Log, TEXT("LifecycleDemoActor [%s]: EndPlay (reason=%d)"),
        *GetName(), static_cast<int32>(EndPlayReason));

    // Demonstrate weak pointer validity check: at EndPlay, the actor is still
    // alive, so WeakSelfReference should resolve.
    if (WeakSelfReference.IsValid())
    {
        UE_LOG(LogTemp, Log, TEXT("LifecycleDemoActor [%s]: WeakSelf is still valid at EndPlay"),
            *GetName());
    }

    Super::EndPlay(EndPlayReason);
}

void ALifecycleDemoActor::Destroyed()
{
    UE_LOG(LogTemp, Log, TEXT("LifecycleDemoActor [%s]: Destroyed"), *GetName());
    Super::Destroyed();
}

void ALifecycleDemoActor::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    // Simple rotation to prove ticking is active.
    FRotator CurrentRotation = GetActorRotation();
    CurrentRotation.Yaw += 90.0f * DeltaTime;
    SetActorRotation(CurrentRotation);
}

ALifecycleDemoActor* ALifecycleDemoActor::SpawnInWorld(
    UObject* WorldContextObject, FVector Location, FRotator Rotation)
{
    UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull);
    if (World == nullptr)
    {
        UE_LOG(LogTemp, Error, TEXT("SpawnInWorld: World context is null"));
        return nullptr;
    }

    FActorSpawnParameters SpawnParams;
    SpawnParams.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
    SpawnParams.bNoFail = true;

    ALifecycleDemoActor* NewActor = World->SpawnActor<ALifecycleDemoActor>(
        ALifecycleDemoActor::StaticClass(),
        Location,
        Rotation,
        SpawnParams);

    if (NewActor == nullptr)
    {
        UE_LOG(LogTemp, Error, TEXT("SpawnInWorld: SpawnActor returned null"));
    }

    return NewActor;
}
```

The component attachment hierarchy is governed by `USceneComponent::AttachToComponent`, which accepts a parent component, a socket name (for skeletal mesh bone sockets), and a set of attachment rules that control how transforms are reconciled during the attachment operation. The `FAttachmentTransformRules` struct encodes three independent rule enums—one for location, one for rotation, one for scale—each of which can be `KeepRelative` (preserve the component's current relative offset), `KeepWorld` (preserve the component's current world-space transform, recomputing the relative offset against the new parent), or `SnapToTarget` (reset to zero relative offset, snapping to the parent). The `KeepWorld` rule is the safest choice when reparenting a component that is already placed in the world, because it prevents the component from visually jumping to a new position. The `SnapToTarget` rule is used when you want a child to inherit the parent's transform exactly, which is common for weapons attached to a character's hand socket.

The following diagram illustrates the attachment graph for a typical character actor, showing how the transform hierarchy flows from the actor's root component down through skeletal mesh bones to attached child meshes:

```
ACharacter
 │
 ├── CapsuleComponent (RootComponent, USceneComponent)
 │    │  Transform: World position of the actor
 │    │
 │    ├── ArrowComponent (editor-only visualization)
 │    │
 │    └── Mesh (USkeletalMeshComponent)
 │         │  Transform: relative offset inside capsule
 │         │
 │         ├── Bone "hand_r" (socket)
 │         │    │
 │         │    └── WeaponMesh (UStaticMeshComponent)
 │         │         Transform: relative to hand_r socket
 │         │
 │         └── Bone "head" (socket)
 │              │
 │              └── HelmetMesh (UStaticMeshComponent)
 │                   Transform: relative to head socket
 │
 └── CharacterMovementComponent (UActorComponent, non-scene)
      No transform; drives physics-based movement on the capsule.
```

When the character moves, the `ACharacter` class calls `SetActorLocation` on the capsule, which updates the capsule's world transform. The skeletal mesh component, being a child of the capsule, receives the transform update through `UpdateComponentToWorld`, which recomputes its world transform from the parent's world transform and its own relative transform. The skeletal mesh's bone transforms are then computed from animation, and the bone sockets' world transforms are derived from the bone matrices. The weapon mesh, attached to the `hand_r` socket, receives a final world transform that is the composition of the actor's world transform, the mesh's relative transform, the bone's animated transform, and the weapon's relative-to-socket transform. This composition is a matrix multiplication chain evaluated every frame, and its cost scales linearly with the depth of the attachment tree.

The ticking system is organized into tick groups, which are execution phases within a single frame. The engine processes ticks in the following order: `TG_PrePhysics` (game logic that should run before the physics solver), `TG_DuringPhysics` (components that can tick concurrently with the physics solver, running on parallel threads), `TG_PostPhysics` (game logic that should react to physics results), `TG_PostUpdateWork` (late updates, such as camera follow), and `TG_EndPhysics` (finalization). Components declare their preferred tick group by setting `PrimaryComponentTick.TickGroup`, and the engine's task graph constructs a directed acyclic graph of tick functions for the frame, respecting prerequisites declared via `AddTickPrerequisite`. This dependency graph is what allows a camera component to guarantee it ticks after the character movement component has finished, without the camera needing to poll the movement component's state.

The following complete component class demonstrates manual tick group configuration and tick prerequisite registration. It is a camera follow component that ticks in `TG_PostUpdateWork`, after the character's movement has resolved, and it registers a prerequisite on the owning character's movement component.

```cpp
// CameraFollowComponent.h
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CameraFollowComponent.generated.h"

UCLASS(ClassGroup = (Lesson3), meta = (BlueprintSpawnableComponent))
class UCameraFollowComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UCameraFollowComponent();

    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lesson3")
    float FollowLerpSpeed = 6.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lesson3")
    FVector FollowOffset = FVector(0.0f, 0.0f, 200.0f);

protected:
    // The target actor we follow. Stored as weak so we never prevent GC.
    TWeakObjectPtr<AActor> FollowTarget;
};
```

```cpp
// CameraFollowComponent.cpp
#include "CameraFollowComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

UCameraFollowComponent::UCameraFollowComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = true;

    // Tick after physics and movement have resolved for this frame.
    PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void UCameraFollowComponent::BeginPlay()
{
    Super::BeginPlay();

    // If we are owned by a pawn, follow that pawn.
    APawn* OwningPawn = Cast<APawn>(GetOwner());
    if (OwningPawn != nullptr)
    {
        FollowTarget = OwningPawn;

        // Register a tick prerequisite on the pawn's movement component so
        // that our TickComponent always runs after movement has updated the
        // pawn's location this frame.
        UCharacterMovementComponent* MoveComp =
            Cast<UCharacterMovementComponent>(OwningPawn->GetMovementComponent());
        if (MoveComp != nullptr)
        {
            PrimaryComponentTick.AddTickPrerequisite(MoveComp);
        }
    }
}

void UCameraFollowComponent::TickComponent(float DeltaTime, ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!FollowTarget.IsValid())
    {
        return;
    }

    AActor* Target = FollowTarget.Get();
    if (Target == nullptr)
    {
        return;
    }

    // Interpolate this component's owner toward the follow target plus offset.
    FVector DesiredLocation = Target->GetActorLocation() + FollowOffset;
    AActor* Owner = GetOwner();
    FVector CurrentLocation = Owner->GetActorLocation();
    FVector Interpolated = FMath::VInterpTo(
        CurrentLocation, DesiredLocation, DeltaTime, FollowLerpSpeed);
    Owner->SetActorLocation(Interpolated);
}
```

World partitioning in Unreal Engine 5 replaces the traditional sublevel streaming model with a single continuous world divided into a grid of runtime cells. Each cell is a `UWorldPartitionRuntimeCell` object that holds a set of actors and their bundled assets. The `UWorldPartition` subsystem manages cell loading and unloading based on streaming sources, which are objects in the world that declare a load radius and a set of data layer states they care about. The player controller is automatically registered as a streaming source, and you can register additional sources (cameras, AI anchors, scripted events) to preload regions the player is about to enter.

The data layer system complements world partitioning by allowing cells to be subdivided by logical state. A data layer is a named filter that can be in one of three states: `Loaded`, `Unloaded`, or `Runtime`. An actor can belong to multiple data layers, and the streaming system only loads an actor if all of its data layers are in the `Loaded` state. This is the mechanism that powers time-of-day world variations, quest-gated area access, and difficulty-tiered content.

The following C++ code demonstrates how to programmatically control data layer states at runtime. It is a complete actor that, when interacted with, toggles a data layer on or off, causing the world partition system to load or unload the associated actors.

```cpp
// DataLayerControllerActor.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Engine/WorldPartition.h"
#include "WorldPartition/DataLayer/DataLayerManager.h"
#include "WorldPartition/DataLayer/WorldDataLayers.h"
#include "DataLayerControllerActor.generated.h"

UCLASS(BlueprintType, Blueprintable, Category = "Lesson3")
class ADataLayerControllerActor : public AActor
{
    GENERATED_BODY()

public:
    ADataLayerControllerActor();

    virtual void BeginPlay() override;

    // Toggle a data layer between Loaded and Unloaded states.
    UFUNCTION(BlueprintCallable, Category = "Lesson3")
    void ToggleDataLayerState();

    // Set a data layer to a specific state.
    UFUNCTION(BlueprintCallable, Category = "Lesson3")
    void SetDataLayerState(FName DataLayerName, EDataLayerState NewState);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lesson3")
    FName TargetDataLayerName = TEXT("QuestAreaLayer");

protected:
    bool bLayerCurrentlyLoaded = false;
};
```

```cpp
// DataLayerControllerActor.cpp
#include "DataLayerControllerActor.h"

ADataLayerControllerActor::ADataLayerControllerActor()
{
    PrimaryActorTick.bCanEverTick = false;
}

void ADataLayerControllerActor::BeginPlay()
{
    Super::BeginPlay();
    bLayerCurrentlyLoaded = true;
}

void ADataLayerControllerActor::ToggleDataLayerState()
{
    EDataLayerState TargetState =
        bLayerCurrentlyLoaded ? EDataLayerState::Unloaded : EDataLayerState::Loaded;
    SetDataLayerState(TargetDataLayerName, TargetState);
    bLayerCurrentlyLoaded = !bLayerCurrentlyLoaded;
}

void ADataLayerControllerActor::SetDataLayerState(FName DataLayerName,
    EDataLayerState NewState)
{
    UWorld* World = GetWorld();
    if (World == nullptr)
    {
        UE_LOG(LogTemp, Error, TEXT("SetDataLayerState: World is null"));
        return;
    }

    UWorldPartition* WorldPartition = World->GetWorldPartition();
    if (WorldPartition == nullptr)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("SetDataLayerState: World has no WorldPartition. "
                 "Ensure World Partition is enabled in World Settings."));
        return;
    }

    UDataLayerManager* DataLayerManager = WorldPartition->GetDataLayerManager();
    if (DataLayerManager == nullptr)
    {
        UE_LOG(LogTemp, Error, TEXT("SetDataLayerState: DataLayerManager is null"));
        return;
    }

    UDataLayerInstance* DataLayerInstance =
        DataLayerManager->GetDataLayerInstanceFromName(DataLayerName);
    if (DataLayerInstance == nullptr)
    {
        UE_LOG(LogTemp, Error,
            TEXT("SetDataLayerState: Data layer '%s' not found"), *DataLayerName.ToString());
        return;
    }

    // Set the data layer state via the manager's async interface.
    DataLayerManager->SetDataLayerInstanceRuntimeState(DataLayerInstance, NewState);

    UE_LOG(LogTemp, Log,
        TEXT("SetDataLayerState: '%s' -> %s"),
        *DataLayerName.ToString(),
        *UEnum::GetValueAsString(NewState));
}
```

The streaming system operates asynchronously. When you set a data layer to `Loaded`, the engine does not immediately load the actors. It enqueues load requests that are processed by the `FStreamableManager` on background threads, using the async loading machinery in the `FAsyncLoadingThread`. The loaded actors are then registered with the world on the game thread during the next frame's `UpdateLevelStreaming` pass. This means there is a latency of several frames between requesting a data layer state change and the actors being available in the world, and your gameplay logic must account for this delay. The `UDataLayerManager` provides callbacks and delegates that fire when the state transition completes, and you should bind to these delegates rather than polling actor existence.

The traditional level streaming model, which predates world partitioning, uses `ULevelStreaming` objects to wrap sublevels. Each `ULevelStreaming` has a `LevelTransform` that offsets the entire sublevel's content, a `LevelColor` for editor visualization, and a state machine that cycles through `Removed`, `Unloaded`, `Loading`, `LoadedNotVisible`, `MakingVisible`, `LoadedVisible`, `MakingInvisible`, and back to `LoadedNotVisible`. The `LoadLevel` and `UnloadLevel` blueprint nodes drive this state machine, and the `FlushLevelStreaming` function forces a synchronous resolution of all pending streaming operations, which can cause a frame hitch if the pending load set is large.

The following complete code demonstrates manual level streaming control via C++, including the correct pattern for responding to the streaming completion delegate:

```cpp
// LevelStreamingControllerActor.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Engine/LevelStreaming.h"
#include "LevelStreamingControllerActor.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
    FOnLevelStreamingComplete, FName, LevelPackageName);

UCLASS(BlueprintType, Blueprintable, Category = "Lesson3")
class ALevelStreamingControllerActor : public AActor
{
    GENERATED_BODY()

public:
    ALevelStreamingControllerActor();

    // Load a sublevel by its short name (e.g., "SubLevel_QuestRoom").
    UFUNCTION(BlueprintCallable, Category = "Lesson3")
    void LoadSubLevel(FName LevelShortName);

    // Unload a sublevel by its short name.
    UFUNCTION(BlueprintCallable, Category = "Lesson3")
    void UnloadSubLevel(FName LevelShortName);

    // Force-synchronously flush all pending streaming operations.
    // Use sparingly: this blocks the game thread until all loads complete.
    UFUNCTION(BlueprintCallable, Category = "Lesson3",
        meta = (DisplayName = "Flush Streaming (Synchronous)"))
    void FlushStreamingSynchronous();

    UPROPERTY(BlueprintAssignable, Category = "Lesson3")
    FOnLevelStreamingComplete OnLevelStreamingComplete;

protected:
    UFUNCTION()
    void HandleStreamingStateChange(ULevelStreaming* LevelStreaming,
        ULevel* LoadedLevel, ULevel::EStreamLoadingState LoadingState);
};
```

```cpp
// LevelStreamingControllerActor.cpp
#include "LevelStreamingControllerActor.h"
#include "Engine/Level.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/PackageName.h"

ALevelStreamingControllerActor::ALevelStreamingControllerActor()
{
    PrimaryActorTick.bCanEverTick = false;
}

void ALevelStreamingControllerActor::LoadSubLevel(FName LevelShortName)
{
    UWorld* World = GetWorld();
    if (World == nullptr)
    {
        return;
    }

    // Resolve the full package name for the sublevel.
    FString LevelPackageName = FPackageName::ExportTextPathToObjectPath(
        World->GetFullName().LeftChop(World->GetFullName().Find(TEXT(":"))) +
        TEXT("_") + LevelShortName.ToString());

    // Convert the short name to a package path. For a persistent level named
    // "/Game/Maps/WorldMap", a sublevel named "QuestRoom" would resolve to
    // "/Game/Maps/WorldMap_QuestRoom".
    FString BasePackage = FPackageName::GetLongPackagePath(World->GetPackage()->GetName());
    FString FullPackageName = BasePackage + TEXT("/") + LevelShortName.ToString();

    // Check if a streaming level for this package already exists.
    bool bAlreadyStreaming = false;
    for (ULevelStreaming* ExistingLevel : World->GetStreamingLevels())
    {
        if (ExistingLevel != nullptr &&
            ExistingLevel->GetWorldAssetPackageName() == FullPackageName)
        {
            if (ExistingLevel->ShouldBeLoaded() || ExistingLevel->IsLevelLoaded())
            {
                bAlreadyStreaming = true;
            }
            break;
        }
    }

    if (!bAlreadyStreaming)
    {
        // Load the level asynchronously using the ULevelStreaming dynamic API.
        ULevelStreaming* StreamingLevel =
            UGameplayStatics::GetStreamingLevel(World, FName(*FullPackageName));
        if (StreamingLevel == nullptr)
        {
            // The level is not part of the persistent level's streaming list.
            // Use LoadStreamLevel to add it dynamically.
            FLatentActionInfo LatentInfo;
            LatentInfo.CallbackTarget = this;
            LatentInfo.ExecutionFunction =
                TEXT("HandleStreamingStateChange");
            LatentInfo.UUID = 1;
            LatentInfo.Linkage = 0;

            UGameplayStatics::LoadStreamLevelBySoftObjectPtr(
                World,
                TSoftObjectPtr<UWorld>(FSoftObjectPath(FullPackageName)),
                true,   // bMakeVisibleAfterLoad
                true,   // bShouldBlockOnLoad (use false for async)
                LatentInfo);

            UE_LOG(LogTemp, Log,
                TEXT("LoadSubLevel: requested load of '%s'"), *FullPackageName);
        }
        else
        {
            StreamingLevel->SetShouldBeLoaded(true);
            StreamingLevel->SetShouldBeVisible(true);
        }
    }
}

void ALevelStreamingControllerActor::UnloadSubLevel(FName LevelShortName)
{
    UWorld* World = GetWorld();
    if (World == nullptr)
    {
        return;
    }

    FString BasePackage = FPackageName::GetLongPackagePath(World->GetPackage()->GetName());
    FString FullPackageName = BasePackage + TEXT("/") + LevelShortName.ToString();

    ULevelStreaming* StreamingLevel =
        UGameplayStatics::GetStreamingLevel(World, FName(*FullPackageName));

    if (StreamingLevel != nullptr)
    {
        FLatentActionInfo LatentInfo;
        LatentInfo.CallbackTarget = this;
        LatentInfo.ExecutionFunction = TEXT("HandleStreamingStateChange");
        LatentInfo.UUID = 2;
        LatentInfo.Linkage = 0;

        UGameplayStatics::UnloadStreamLevelBySoftObjectPtr(
            World,
            TSoftObjectPtr<UWorld>(FSoftObjectPath(FullPackageName)),
            LatentInfo,
            true);   // bShouldBlockOnUnload

        UE_LOG(LogTemp, Log,
            TEXT("UnloadSubLevel: requested unload of '%s'"), *FullPackageName);
    }
}

void ALevelStreamingControllerActor::FlushStreamingSynchronous()
{
    UWorld* World = GetWorld();
    if (World != nullptr)
    {
        World->FlushLevelStreaming(EFlushLevelStreamingType::Full);
        UE_LOG(LogTemp, Log, TEXT("FlushStreamingSynchronous: flush complete"));
    }
}

void ALevelStreamingControllerActor::HandleStreamingStateChange(
    ULevelStreaming* LevelStreaming, ULevel* LoadedLevel,
    ULevel::EStreamLoadingState LoadingState)
{
    if (LevelStreaming != nullptr)
    {
        FName LevelName = FName(*LevelStreaming->GetWorldAssetPackageName());
        UE_LOG(LogTemp, Log,
            TEXT("HandleStreamingStateChange: '%s' state=%d"),
            *LevelName.ToString(), static_cast<int32>(LoadingState));

        if (LoadingState == ULevel::EStreamLoadingState::Loaded &&
            OnLevelStreamingComplete.IsBound())
        {
            OnLevelStreamingComplete.Broadcast(LevelName);
        }
    }
}
```

## 3. High-Performance Optimization & Failure Modes

The most common performance pathology in Unreal Engine actor systems is unnecessary ticking. Every component that has `bCanEverTick` set to true is registered with the engine's tick function manager, and even if the component does minimal work in its `TickComponent` override, the overhead of dispatching the tick function—checking prerequisites, setting up the task graph node, and invoking the virtual call—accumulates across thousands of components. The fix is to disable ticking by default and enable it only when needed. In the component constructor, set `PrimaryComponentTick.bCanEverTick = false` or `bStartWithTickEnabled = false`, and at runtime, call `SetComponentTickEnabled(true)` when the component needs to update and `SetComponentTickEnabled(false)` when it is done. For actors that only need to tick in response to specific events, consider using a timer via `FTimerHandle` and `GetWorld()->GetTimerManager().SetTimer`, which is cheaper than a per-frame tick because it only fires on the specified interval and does not participate in the tick dependency graph.

The second most common pathology is synchronous loading. Any call to `LoadObject` or `StaticLoadObject` on the game thread stalls that thread until the load completes, and for large assets, this can take tens or hundreds of milliseconds. The engine's `FStreamableManager` provides `RequestAsyncLoad`, which loads assets on background threads and invokes a delegate when complete. The soft reference system—`TSoftObjectPtr<T>` and `TSoftClassPtr<T>`—stores a `FSoftObjectPath` (a package name and an object name within that package) and resolves the asset on demand. When you use `TSoftObjectPtr`, the asset is not loaded until you call `ResolveObject` or `LoadSynchronous`, and the latter still stalls. The correct pattern for async loading via soft pointers is to use the `UAssetManager` or the `FStreamableManager` to request the load, bind a delegate to the completion callback, and only dereference the pointer after the delegate fires. The code below demonstrates this pattern in a complete, compilable component.

```cpp
// AsyncAssetLoaderComponent.h
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/StreamableManager.h"
#include "AsyncAssetLoaderComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
    FOnAssetLoaded, UObject*, LoadedAsset);

UCLASS(ClassGroup = (Lesson3), meta = (BlueprintSpawnableComponent))
class UAsyncAssetLoaderComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UAsyncAssetLoaderComponent();

    UPROPERTY(BlueprintAssignable, Category = "Lesson3")
    FOnAssetLoaded OnAssetLoaded;

    // Request async load of a soft-referenced asset.
    UFUNCTION(BlueprintCallable, Category = "Lesson3")
    void RequestAsyncLoad(TSoftObjectPtr<UObject> SoftAsset);

protected:
    FStreamableManager StreamableManager;
    TSharedPtr<FStreamableHandle> CurrentLoadHandle;

    void HandleLoadComplete(FString AssetName);
};
```

```cpp
// AsyncAssetLoaderComponent.cpp
#include "AsyncAssetLoaderComponent.h"
#include "Engine/AssetManager.h"

UAsyncAssetLoaderComponent::UAsyncAssetLoaderComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UAsyncAssetLoaderComponent::RequestAsyncLoad(TSoftObjectPtr<UObject> SoftAsset)
{
    if (!SoftAsset.IsValid())
    {
        UE_LOG(LogTemp, Warning,
            TEXT("RequestAsyncLoad: Soft pointer path is empty"));
        return;
    }

    // If already loaded, resolve immediately and broadcast.
    UObject* AlreadyLoaded = SoftAsset.Get();
    if (AlreadyLoaded != nullptr)
    {
        UE_LOG(LogTemp, Log,
            TEXT("RequestAsyncLoad: '%s' was already loaded"),
            *SoftAsset.ToString());
        OnAssetLoaded.Broadcast(AlreadyLoaded);
        return;
    }

    FString AssetPathString = SoftAsset.ToString();

    // Request async load via the streamable manager. The delegate fires on the
    // game thread when the load completes.
    TArray<FSoftObjectPath> AssetsToLoad;
    AssetsToLoad.Add(SoftAsset.ToSoftObjectPath());

    CurrentLoadHandle = StreamableManager.RequestAsyncLoad(
        AssetsToLoad,
        FStreamableDelegate::CreateLambda([this, AssetPathString]()
        {
            HandleLoadComplete(AssetPathString);
        }));

    if (!CurrentLoadHandle.IsValid())
    {
        UE_LOG(LogTemp, Error,
            TEXT("RequestAsyncLoad: RequestAsyncLoad failed for '%s'"),
            *AssetPathString);
    }
}

void UAsyncAssetLoaderComponent::HandleLoadComplete(FString AssetName)
{
    if (!CurrentLoadHandle.IsValid())
    {
        UE_LOG(LogTemp, Error,
            TEXT("HandleLoadComplete: handle is invalid for '%s'"), *AssetName);
        return;
    }

    // Get the loaded object from the handle.
    TArray<UObject*> LoadedObjects;
    CurrentLoadHandle->GetLoadedAssets(LoadedObjects);

    if (LoadedObjects.Num() > 0 && OnAssetLoaded.IsBound())
    {
        OnAssetLoaded.Broadcast(LoadedObjects[0]);
        UE_LOG(LogTemp, Log,
            TEXT("HandleLoadComplete: broadcast '%s'"), *AssetName);
    }
    else
    {
        UE_LOG(LogTemp, Error,
            TEXT("HandleLoadComplete: no objects loaded for '%s'"), *AssetName);
    }

    CurrentLoadHandle.Reset();
}
```

A subtler performance concern is the garbage collector's behavior under high actor counts. The Unreal GC is a parallel, incremental, cluster-based collector. It traces the `UObject` reference graph from root set members—static arrays of `UObject*` marked as roots, `UPROPERTY` members of `UClass` objects, and `FRootSet` calls—through all reachable objects, and collects anything not reachable. For large worlds with thousands of actors, the trace cost can dominate frame time if the GC runs too frequently. The `gc.NumSteadyFramePurge` console variable controls how many steady frames must pass before another GC pass runs, and `gc.TimeBetweenPurgesPendingKill` controls the minimum interval. For worlds with many short-lived actors (projectiles, debris, particle effects), clustering can reduce trace cost by treating a set of objects as a single GC node: when the cluster root is reachable, all cluster members are assumed reachable without individual tracing. The `UClass` property `bSparseClassData` and the `UPROPERTY` macro's `meta = (ClutterFilter)` flag reduce the per-object trace overhead by excluding certain members from the default scan.

The failure modes of actor lifecycle management are concentrated at three points: stale references after destruction, component registration races during spawning, and tick ordering violations. A stale reference occurs when you hold a raw `UObject*` to an actor that has been destroyed but not yet collected. The actor's memory is still mapped, its `UObject` header still has its `UClass` pointer, and calling methods on it may appear to work briefly, but the actor's components have been unregistered and its world pointer may be null. The defense is to use `TWeakObjectPtr<AActor>` for all references that cross ownership boundaries, and to check `IsValid()` or `IsPendingKill()` before dereferencing. The `IsValid` function is more thorough than a null check: it returns false for both null pointers and objects that have been marked for destruction.

The component registration race occurs when a component attempts to access another component during `BeginPlay` before the second component has been registered. The engine registers components in the order they appear in the actor's `OwnedComponents` set, which is typically the order they were created in the constructor, but `BeginPlay` propagation can interleave with script-driven component creation if a Blueprint adds components in its construction script. The defense is to use `Get ComponentsByClass` or `FindComponentByClass` with null checks, and to defer cross-component initialization to `PostInitializeComponents` or a custom `PostActorInitialized` event, which runs after all auto-registered components are ready.

Tick ordering violations manifest as one-frame-latency bugs, where a component reads a value that was computed by another component but that computation has not run yet for the current frame. The defense is to declare tick prerequisites using `AddTickPrerequisite` on the dependent component's tick function, passing the prerequisite component's tick function. This inserts an edge into the task graph's tick DAG, guaranteeing that the prerequisite ticks first. If you are working with physics, be aware that `TG_DuringPhysics` tick functions run on parallel threads concurrent with the physics solver, and reading physics state during that window may produce results from either the previous frame or the current frame depending on thread timing. For deterministic reads of physics state, tick in `TG_PostPhysics` instead.

The final failure mode to guard against is the world partition streaming stall. When the player crosses a cell boundary at high speed, the streaming system may not have finished loading the target cell's actors, resulting in visible pop-in or, in the worst case, a collision with unloaded geometry. The defense is to increase the streaming source's load radius, to add predictive streaming sources ahead of the player's velocity vector, and to use the `WorldPartitionHysteresisVolume` to create a buffer zone around cells that delays unloading until the player has moved a configurable distance past the cell boundary. For critical gameplay actors that must always be loaded regardless of streaming state, mark them with the `SpatiallyLoaded = false` flag in the World Partition editor, which exempts them from the cell-based streaming logic and keeps them resident in memory permanently.
