import React, { useState } from 'react';
import { Compass, X, ArrowRight, Search } from 'lucide-react';

interface PathwayStep {
  step: number;
  title: string;
  path: string;
  domain: string;
  whyLearnFirst: string;
}

interface PathwayTrack {
  id: string;
  title: string;
  domain: string;
  icon: string;
  description: string;
  steps: PathwayStep[];
}

const CURATED_PATHWAYS: PathwayTrack[] = [
  {
    id: 'systems_kernel_k8s',
    title: 'Systems, Kernel & Cloud-Native Infrastructure',
    domain: 'computing',
    icon: '🐧',
    description: 'From silicon microarchitectures and assembly to Linux kernel internals, eBPF, and Kubernetes control planes.',
    steps: [
      {
        step: 1,
        title: 'CPU Pipelines & Hardware Hazards',
        path: 'engineering/hardware/computer_architecture/01_cpu_pipelines_hazards_and_superscalar',
        domain: 'engineering',
        whyLearnFirst: 'Understand instruction pipelines and branch prediction before writing low-level code.',
      },
      {
        step: 2,
        title: 'x86-64 Calling Conventions & Stack Frames',
        path: 'engineering/hardware/assembly_programming/01_x86_64_calling_conventions_and_stack_frames',
        domain: 'engineering',
        whyLearnFirst: 'Learn how function calls, registers, and memory frames operate on the bare silicon.',
      },
      {
        step: 3,
        title: 'Rust Memory Layout, Ownership & Lifetimes',
        path: 'computing/software/rust_systems/01_memory_layout_ownership_and_lifetimes',
        domain: 'computing',
        whyLearnFirst: 'Master zero-cost memory safety without a garbage collector before touching driver code.',
      },
      {
        step: 4,
        title: 'Linux Virtual Memory & MMU Page Tables',
        path: 'computing/infrastructure/linux_kernel/01_virtual_memory_and_mmu',
        domain: 'computing',
        whyLearnFirst: 'Grasp multi-level paging and kernel space mapping before writing kernel extensions.',
      },
      {
        step: 5,
        title: 'eBPF In-Kernel Virtual Machine & Verifier',
        path: 'computing/infrastructure/ebpf/01_virtual_machine_and_isa',
        domain: 'computing',
        whyLearnFirst: 'Understand sandboxed verification and JIT execution inside Ring 0.',
      },
      {
        step: 6,
        title: 'Character Drivers & Kernel Module Lifecycle',
        path: 'computing/infrastructure/linux_device_drivers/01_kernel_module_lifecycle_and_kbuild',
        domain: 'computing',
        whyLearnFirst: 'Learn how the Linux VFS layer and file operations bind to physical hardware.',
      },
      {
        step: 7,
        title: 'Kubernetes Control Plane & etcd Consensus',
        path: 'computing/infrastructure/kubernetes/01_control_plane_and_etcd',
        domain: 'computing',
        whyLearnFirst: 'See how declarative state machines and Raft quorums orchestrate distributed systems.',
      },
    ],
  },
  {
    id: 'ai_deep_learning_agents',
    title: 'AI, Deep Learning & Autonomous Agents',
    domain: 'computing',
    icon: '🧠',
    description: 'From vector spaces and gradient descent to Transformers, LLMs, fine-tuning, and multi-agent systems.',
    steps: [
      {
        step: 1,
        title: 'Vector Spaces & Matrix Decompositions',
        path: 'formal_sciences/pure_math/linear_algebra/01_vector_spaces_subspaces_and_bases',
        domain: 'formal_sciences',
        whyLearnFirst: 'Essential for representing token embeddings, attention matrices, and tensor weights.',
      },
      {
        step: 2,
        title: 'Supervised Learning & Gradient Descent',
        path: 'computing/ai/foundations_of_ml/01_supervised_vs_unsupervised_learning',
        domain: 'computing',
        whyLearnFirst: 'Grasp convex loss landscapes and backpropagation before training deep architectures.',
      },
      {
        step: 3,
        title: 'Transformer Multi-Head Attention Mechanisms',
        path: 'computing/ai/deep_learning/04_transformer_attention_mechanisms',
        domain: 'computing',
        whyLearnFirst: 'The architectural foundation of all modern generative and language models.',
      },
      {
        step: 4,
        title: 'LLM Tokenization & Pretraining Objectives',
        path: 'computing/ai/large_language_models/01_tokenization_and_pretraining_objectives',
        domain: 'computing',
        whyLearnFirst: 'Understand next-token prediction and context window scaling dynamics.',
      },
      {
        step: 5,
        title: 'Autonomous Agents, ReAct & MCP Protocols',
        path: 'computing/ai/ai_agents/01_react_framework_and_reasoning_loops',
        domain: 'computing',
        whyLearnFirst: 'Learn how LLMs orchestrate tools, inspect external environments, and self-reflect.',
      },
      {
        step: 6,
        title: 'Model Quantization, vLLM & Serving',
        path: 'computing/ai/mlops_and_serving/01_model_quantization_awq_gptq_gguf',
        domain: 'computing',
        whyLearnFirst: 'Deploy 30B+ models locally using AWQ, PagedAttention, and Triton inference engines.',
      },
    ],
  },
  {
    id: 'motorsports_aerodynamics',
    title: 'Motorsports, Aerodynamics & Vehicle Dynamics',
    domain: 'motorsports',
    icon: '🏎️',
    description: 'From contact patch tire physics and Venturi tunnels to trail braking and telemetry CAN bus diagnostics.',
    steps: [
      {
        step: 1,
        title: 'Newtonian Dynamics & Force Equilibrium',
        path: 'natural_sciences/physics/classical_mechanics/01_newtonian_mechanics_and_conservation_laws',
        domain: 'natural_sciences',
        whyLearnFirst: 'Understand inertial mass, centrifugal force, and torque vectors before chassis setup.',
      },
      {
        step: 2,
        title: 'Aerodynamics & Ground Effect Venturi Tunnels',
        path: 'motorsports/driving/aerodynamics/01_lift_drag_polar_and_boundary_layers',
        domain: 'motorsports',
        whyLearnFirst: 'Learn how Bernoulli downforce and vortex sealing keep high-speed cars planted.',
      },
      {
        step: 3,
        title: 'Tire Slip Angles & Contact Patch Mechanics',
        path: 'motorsports/driving/vehicle_dynamics/01_tire_slip_angles_and_contact_patch_physics',
        domain: 'motorsports',
        whyLearnFirst: 'Tire adhesion is the single bottleneck of vehicle handling and lap time.',
      },
      {
        step: 4,
        title: 'Traction Circle & Trail Braking Weight Transfer',
        path: 'motorsports/driving/performance_driving/01_traction_circle_and_weight_transfer',
        domain: 'motorsports',
        whyLearnFirst: 'Master dynamic pitch control on corner entry to maximize front tire bite.',
      },
      {
        step: 5,
        title: 'CAN Bus Architecture & Vehicle Telemetry',
        path: 'computing/security/automotive_cybersecurity/01_can_bus_and_frame_architecture',
        domain: 'computing',
        whyLearnFirst: 'Decode live chassis sensors, wheel speeds, and brake pressures over automotive buses.',
      },
    ],
  },
  {
    id: 'electronics_sdr_hardware',
    title: 'Circuits, Board Electronics & Hardware Security',
    domain: 'engineering',
    icon: '⚡',
    description: 'From lumped element circuits and multimeter diagnostics to SDR radio and hardware reverse engineering.',
    steps: [
      {
        step: 1,
        title: 'Circuit Theory & Complex Impedance (Z)',
        path: 'engineering/circuits/circuit_theory/01_lumped_element_model_and_kcl_kvl',
        domain: 'engineering',
        whyLearnFirst: 'Master Ohm’s and Kirchhoff’s laws before diagnosing circuit boards or RF signals.',
      },
      {
        step: 2,
        title: 'Schematic Reading & Boardview Diagnostics',
        path: 'crafts/maker/electronic_repair/01_schematic_reading_and_boardview_navigation',
        domain: 'crafts',
        whyLearnFirst: 'Learn how to trace voltage rails, locate short circuits, and probe SMD components.',
      },
      {
        step: 3,
        title: 'Software-Defined Radio (SDR) & I/Q Sampling',
        path: 'engineering/hardware/software_defined_radio/01_iq_sampling_and_quadrature_signals',
        domain: 'engineering',
        whyLearnFirst: 'Understand complex baseband signals, Fourier transforms, and wireless demodulation.',
      },
      {
        step: 4,
        title: 'Hardware Hacking: UART, SPI & I2C Bus Sniffing',
        path: 'computing/security/hardware_hacking/01_uart_spi_i2c_bus_analysis',
        domain: 'computing',
        whyLearnFirst: 'Extract firmware and intercept embedded bus communications via logic analyzers.',
      },
    ],
  },
  {
    id: 'music_synthesis_dsp',
    title: 'Music Performance, Synthesizers & Audio DSP',
    domain: 'arts',
    icon: '🎹',
    description: 'From ergonomic piano arm-weight and tonal harmony to subtractive/modular Eurorack synthesis and digital filters.',
    steps: [
      {
        step: 1,
        title: 'Piano Ergonomics & Keyboard Geometries',
        path: 'arts/music_performance/piano/01_hand_posture_and_keyboard_geometries',
        domain: 'arts',
        whyLearnFirst: 'Learn weight transfer and diatonic keyboard topography before composition or synthesis.',
      },
      {
        step: 2,
        title: 'Diatonic Scales, Chords & Key Signatures',
        path: 'arts/composition/music_theory/01_diatonic_scales_and_key_signatures',
        domain: 'arts',
        whyLearnFirst: 'Understand interval relationships, functional harmony, and harmonic tension.',
      },
      {
        step: 3,
        title: 'Oscillator Waveforms & VCF Filter Topologies',
        path: 'arts/music_production/synthesizers/01_oscillators_waveforms_and_harmonics',
        domain: 'arts',
        whyLearnFirst: 'Master subtractive synthesis, harmonic overtone spectra, and resonance slopes.',
      },
      {
        step: 4,
        title: 'Eurorack Control Voltage (1V/Oct) & Modular',
        path: 'arts/music_production/modular_synthesis/01_control_voltage_gate_and_eurorack_standards',
        domain: 'arts',
        whyLearnFirst: 'Explore open architecture CV routing, wavefolding, and generative clock divisions.',
      },
      {
        step: 5,
        title: 'Audio DSP: Discrete-Time Signals & Sampling',
        path: 'arts/music_production/audio_dsp/01_discrete_time_signals_and_sampling',
        domain: 'arts',
        whyLearnFirst: 'Design digital biquad filters, circular delay buffers, and audio plugin DSP in C++.',
      },
    ],
  },
  {
    id: 'logic_game_theory_poker',
    title: 'Formal Logic, Game Theory & Decision Strategy',
    domain: 'humanities',
    icon: '♟️',
    description: 'From formal deduction and Nash equilibria to pot odds, bluffing frequencies, and GTO poker strategy.',
    steps: [
      {
        step: 1,
        title: 'Propositional Logic & Natural Deduction',
        path: 'formal_sciences/discrete_math/logic/01_propositional_logic_and_natural_deduction',
        domain: 'formal_sciences',
        whyLearnFirst: 'Build deductive reasoning and valid inference rules before analyzing strategic payoffs.',
      },
      {
        step: 2,
        title: 'Strategic Form Games & Nash Equilibrium',
        path: 'formal_sciences/applied_math/game_theory/01_strategic_form_and_nash_equilibrium',
        domain: 'formal_sciences',
        whyLearnFirst: 'Understand dominant strategy elimination and simultaneous move equilibria.',
      },
      {
        step: 3,
        title: 'Card Probability, Pot Odds & Expected Value',
        path: 'humanities/games_and_puzzles/card_games/01_poker_probability_pot_odds_and_expected_value',
        domain: 'humanities',
        whyLearnFirst: 'Learn how imperfect information and conditional probability dictate long-run EV.',
      },
      {
        step: 4,
        title: 'Texas Hold’em Preflop Ranges & Position',
        path: 'humanities/games_and_puzzles/texas_holdem_poker/02_preflop_ranges_and_positional_advantage',
        domain: 'humanities',
        whyLearnFirst: 'Position is power: learn range elasticity, 3-betting, and GTO bet polarization.',
      },
    ],
  },
  {
    id: 'biology_genetics_health',
    title: 'Biology, Genetics & Metabolic Health Sciences',
    domain: 'health_sciences',
    icon: '🧬',
    description: 'From molecular genetics and CRISPR to cellular bioenergetics, hypertrophy, and culinary thermodynamics.',
    steps: [
      {
        step: 1,
        title: 'Molecular Genetics & DNA Transcription',
        path: 'natural_sciences/biology/molecular_biology/01_central_dogma_dna_transcription_and_translation',
        domain: 'natural_sciences',
        whyLearnFirst: 'The central dogma of life: understand RNA translation before studying metabolic adaptations.',
      },
      {
        step: 2,
        title: 'CRISPR-Cas9 Precision Gene Editing',
        path: 'natural_sciences/biology/extreme_biology_and_genetics/01_crispr_cas9_and_precision_gene_editing',
        domain: 'natural_sciences',
        whyLearnFirst: 'Learn guide RNA targeting, double-strand breaks, and genetic editing mechanics.',
      },
      {
        step: 3,
        title: 'Exercise Physiology & ATP Energy Systems',
        path: 'health_sciences/physiology/exercise_physiology/01_atp_energy_systems_and_metabolism',
        domain: 'health_sciences',
        whyLearnFirst: 'Grasp the phosphagen, glycolytic, and oxidative energy systems powering muscle contraction.',
      },
      {
        step: 4,
        title: 'Macronutrient Biochemistry & Insulin Dynamics',
        path: 'health_sciences/physiology/nutrition_and_metabolism/01_macronutrient_biochemistry_and_insulin',
        domain: 'health_sciences',
        whyLearnFirst: 'Understand carbohydrate partitioning, glycogen replenishment, and metabolic flexibility.',
      },
      {
        step: 5,
        title: 'Culinary Thermodynamics & Heat Conduction',
        path: 'health_sciences/culinary/culinary_fundamentals/02_heat_transfer_conduction_and_maillard_reaction',
        domain: 'health_sciences',
        whyLearnFirst: 'Apply physical heat transfer, protein denaturation, and the Maillard reaction to cooking.',
      },
    ],
  },
];

interface GraphModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTopic: (path: string) => void;
}

export const GraphModal: React.FC<GraphModalProps> = ({
  isOpen,
  onClose,
  onSelectTopic,
}) => {
  const [selectedDomain, setSelectedDomain] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  if (!isOpen) return null;

  const filteredPathways = CURATED_PATHWAYS.filter((track) => {
    if (selectedDomain !== 'all' && track.domain !== selectedDomain) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const inTitle = track.title.toLowerCase().includes(q);
      const inDesc = track.description.toLowerCase().includes(q);
      const inSteps = track.steps.some(
        (s) => s.title.toLowerCase().includes(q) || s.whyLearnFirst.toLowerCase().includes(q)
      );
      return inTitle || inDesc || inSteps;
    }
    return true;
  });

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="pathways-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="pathway-title-box">
            <Compass size={20} className="pathway-icon" />
            <div>
              <h3>Socratic Learning Pathways Guide</h3>
              <p className="pathway-subtitle">
                Clear progressive study tracks: what to learn first to build unshakeable intuition for complex topics later.
              </p>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose} title="Close Learning Pathways"><X size={16} /></button>
        </div>

        <div className="pathway-filter-bar">
          <div className="filter-group">
            <label>Domain Track:</label>
            <select value={selectedDomain} onChange={(e) => setSelectedDomain(e.target.value)}>
              <option value="all">All Tracks (Cross-Disciplinary Polymath)</option>
              <option value="computing">Computing & Systems</option>
              <option value="engineering">Engineering & Hardware</option>
              <option value="motorsports">Motorsports & Aerodynamics</option>
              <option value="arts">Arts, Sound & DSP</option>
              <option value="health_sciences">Health Sciences & Physiology</option>
              <option value="humanities">Humanities & Game Theory</option>
            </select>
          </div>

          <div className="search-filter-box">
            <Search size={14} className="search-icon" />
            <input
              type="text"
              placeholder="Search concepts e.g. 'eBPF', 'Attention', 'Braking', 'CRISPR'..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pathway-search-input"
            />
            {searchQuery && (
              <button className="clear-btn" onClick={() => setSearchQuery('')}>
                <X size={12} />
              </button>
            )}
          </div>
        </div>

        <div className="pathways-content-scroll">
          {filteredPathways.length === 0 ? (
            <div className="viewer-empty">
              <p>No learning tracks matched your filter. Try searching for broader terms.</p>
            </div>
          ) : (
            <div className="tracks-list">
              {filteredPathways.map((track) => (
                <div key={track.id} className="track-card">
                  <div className="track-header">
                    <span className="track-emoji">{track.icon}</span>
                    <div className="track-header-text">
                      <h4 className="track-title">{track.title}</h4>
                      <p className="track-desc">{track.description}</p>
                    </div>
                  </div>

                  <div className="track-steps-timeline">
                    {track.steps.map((st, idx) => (
                      <div key={idx} className="timeline-step-row">
                        <div className="step-indicator">
                          <span className="step-num">{st.step}</span>
                          {idx < track.steps.length - 1 && <div className="step-line" />}
                        </div>

                        <div className="step-card">
                          <div className="step-card-header">
                            <span className="step-domain-tag">{st.domain.replace(/_/g, ' ')}</span>
                            <span className="step-tag">Prerequisite Stage</span>
                          </div>

                          <h5 className="step-unit-title">{st.title}</h5>
                          <p className="step-rationale">
                            <strong>Why Learn First:</strong> {st.whyLearnFirst}
                          </p>

                          <button
                            className="btn btn-secondary-sm step-study-btn"
                            onClick={() => {
                              onSelectTopic(st.path);
                              onClose();
                            }}
                            title={`Jump directly to study ${st.title}`}
                          >
                            <span>Study This Topic</span>
                            <ArrowRight size={12} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
