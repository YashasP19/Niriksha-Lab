import { create } from 'zustand';
import type {
  DemoCaseResponse,
  ModelsResponse,
  OrchestrationResponse,
  UploadedFileInput,
} from '../types/api';
import { api } from '../api/client';
import { buildDemoResponse, DEMO_INPUT } from '../api/demoData';

export type AgentStatus = 'idle' | 'running' | 'done';

interface OrchestrationState {
  models: ModelsResponse | null;
  selectedModel: string | null;
  demoCase: DemoCaseResponse | null;
  backendAvailable: boolean;

  errorLog: string;
  specExcerpt: string;
  designImageB64: string;
  testedImageB64: string;
  errorLogFile: UploadedFileInput | null;
  designImageFile: UploadedFileInput | null;
  testedImageFile: UploadedFileInput | null;
  specFiles: UploadedFileInput[];
  designReferenceFiles: UploadedFileInput[];

  isRunning: boolean;
  agentStatuses: AgentStatus[];
  revealedAgents: number;
  currentAgentName: string;

  result: OrchestrationResponse | null;
  error: string | null;

  highlightedBoxLabel: string | null;
  highlightedSpecIdx: number | null;
  expandedAgentIdx: number | null;
  inputCollapsed: boolean;

  fetchModels: () => Promise<void>;
  fetchDemoCase: () => Promise<void>;
  loadDemo: () => void;
  setSelectedModel: (m: string) => void;
  setErrorLog: (v: string) => void;
  setSpecExcerpt: (v: string) => void;
  setDesignImage: (b64: string) => void;
  setTestedImage: (b64: string) => void;
  setErrorLogFile: (f: UploadedFileInput | null) => void;
  setDesignImageFile: (f: UploadedFileInput | null) => void;
  setTestedImageFile: (f: UploadedFileInput | null) => void;
  addSpecFile: (f: UploadedFileInput) => void;
  removeSpecFile: (fileId: string) => void;
  addDesignReferenceFile: (f: UploadedFileInput) => void;
  removeDesignReferenceFile: (fileId: string) => void;
  runDemo: () => Promise<void>;
  runCustom: () => Promise<void>;
  setHighlightedBoxLabel: (label: string | null) => void;
  setHighlightedSpecIdx: (idx: number | null) => void;
  setExpandedAgentIdx: (idx: number | null) => void;
  setInputCollapsed: (v: boolean) => void;
  reset: () => void;
}

export const AGENT_NAMES = [
  'Error Analyzer',
  'Spec Checker',
  'CAD Mapper',
  'Defect Inspector',
  'Spec Resolution',
];

const INITIAL_STATUSES: AgentStatus[] = ['idle', 'idle', 'idle', 'idle', 'idle'];

/**
 * Staged reveal with parallel fan-out for agents 2a+2b (indices 1,2).
 * Agent 1 -> (Agent 2a || Agent 2b) -> Agent 3 -> Agent 4
 */
function stagedReveal(
  set: (fn: (s: OrchestrationState) => Partial<OrchestrationState>) => void,
) {
  const D = 1200;
  // Agent 1 done
  setTimeout(() => {
    set((s) => {
      const st = [...s.agentStatuses] as AgentStatus[];
      st[0] = 'done';
      return { agentStatuses: st };
    });
  }, D * 0.7);
  // Agent 2a + 2b start simultaneously
  setTimeout(() => {
    set((s) => {
      const st = [...s.agentStatuses] as AgentStatus[];
      st[0] = 'done'; st[1] = 'running'; st[2] = 'running';
      return { agentStatuses: st, revealedAgents: 3, currentAgentName: 'Spec Checker + CAD Mapper' };
    });
  }, D);
  // Agent 2a + 2b done simultaneously
  setTimeout(() => {
    set((s) => {
      const st = [...s.agentStatuses] as AgentStatus[];
      st[1] = 'done'; st[2] = 'done';
      return { agentStatuses: st };
    });
  }, D + D * 0.7);
  // Agent 3 start
  setTimeout(() => {
    set((s) => {
      const st = [...s.agentStatuses] as AgentStatus[];
      st[0] = 'done'; st[1] = 'done'; st[2] = 'done'; st[3] = 'running';
      return { agentStatuses: st, revealedAgents: 4, currentAgentName: AGENT_NAMES[3] };
    });
  }, D * 2);
  // Agent 3 done
  setTimeout(() => {
    set((s) => {
      const st = [...s.agentStatuses] as AgentStatus[];
      st[3] = 'done';
      return { agentStatuses: st };
    });
  }, D * 2 + D * 0.7);
  // Agent 4 start
  setTimeout(() => {
    set((s) => {
      const st = [...s.agentStatuses] as AgentStatus[];
      st[0] = 'done'; st[1] = 'done'; st[2] = 'done'; st[3] = 'done'; st[4] = 'running';
      return { agentStatuses: st, revealedAgents: 5, currentAgentName: AGENT_NAMES[4] };
    });
  }, D * 3);
  // Agent 4 done
  setTimeout(() => {
    set((s) => {
      const st = [...s.agentStatuses] as AgentStatus[];
      st[4] = 'done';
      return { agentStatuses: st };
    });
  }, D * 3 + D * 0.7);
}

export const useOrchestrationStore = create<OrchestrationState>((set, get) => ({
  models: null,
  selectedModel: null,
  demoCase: null,
  backendAvailable: false,
  errorLog: '',
  specExcerpt: '',
  designImageB64: '',
  testedImageB64: '',
  errorLogFile: null,
  designImageFile: null,
  testedImageFile: null,
  specFiles: [],
  designReferenceFiles: [],
  isRunning: false,
  agentStatuses: [...INITIAL_STATUSES],
  revealedAgents: 0,
  currentAgentName: '',
  result: null,
  error: null,
  highlightedBoxLabel: null,
  highlightedSpecIdx: null,
  expandedAgentIdx: null,
  inputCollapsed: false,

  fetchModels: async () => {
    try {
      const models = await api.models();
      set(() => ({ models, selectedModel: models.recommended_model, backendAvailable: true }));
    } catch {
      set(() => ({ backendAvailable: false }));
    }
  },

  fetchDemoCase: async () => {
    try {
      const demoCase = await api.demoCase();
      set(() => ({ demoCase }));
    } catch { /* non-critical */ }
  },

  loadDemo: () => {
    const dc = get().demoCase;
    if (dc) {
      set(() => ({
        errorLog: dc.request.input.error_log,
        specExcerpt: dc.request.input.spec_excerpt ?? '',
        designImageB64: '',
        testedImageB64: '',
        errorLogFile: null,
        designImageFile: null,
        testedImageFile: null,
        specFiles: [],
        designReferenceFiles: [],
      }));
    } else {
      set(() => ({
        errorLog: DEMO_INPUT.errorLog,
        specExcerpt: DEMO_INPUT.specExcerpt,
        designImageB64: '',
        testedImageB64: '',
        errorLogFile: null,
        designImageFile: null,
        testedImageFile: null,
        specFiles: [],
        designReferenceFiles: [],
      }));
    }
  },

  setSelectedModel: (m) => set(() => ({ selectedModel: m })),
  setErrorLog: (v) => set(() => ({ errorLog: v })),
  setSpecExcerpt: (v) => set(() => ({ specExcerpt: v })),
  setDesignImage: (b64) => set(() => ({ designImageB64: b64 })),
  setTestedImage: (b64) => set(() => ({ testedImageB64: b64 })),
  setErrorLogFile: (f) => set(() => ({ errorLogFile: f })),
  setDesignImageFile: (f) => set(() => ({ designImageFile: f })),
  setTestedImageFile: (f) => set(() => ({ testedImageFile: f })),
  addSpecFile: (f) => set((state) => ({ specFiles: [...state.specFiles, f] })),
  removeSpecFile: (fileId) => set((state) => ({
    specFiles: state.specFiles.filter((file) => file.file_id !== fileId),
  })),
  addDesignReferenceFile: (f) => set((state) => ({ designReferenceFiles: [...state.designReferenceFiles, f] })),
  removeDesignReferenceFile: (fileId) => set((state) => ({
    designReferenceFiles: state.designReferenceFiles.filter((file) => file.file_id !== fileId),
  })),
  setHighlightedBoxLabel: (label) => set(() => ({ highlightedBoxLabel: label })),
  setHighlightedSpecIdx: (idx) => set(() => ({ highlightedSpecIdx: idx })),
  setExpandedAgentIdx: (idx) => set(() => ({ expandedAgentIdx: idx })),
  setInputCollapsed: (v) => set(() => ({ inputCollapsed: v })),

  runDemo: async () => {
    set(() => ({
      isRunning: true, error: null, result: null,
      agentStatuses: ['running', 'idle', 'idle', 'idle', 'idle'] as AgentStatus[],
      revealedAgents: 1, currentAgentName: AGENT_NAMES[0],
      highlightedBoxLabel: null, highlightedSpecIdx: null, expandedAgentIdx: null,
      inputCollapsed: true,
    }));

    if (!get().errorLog) {
      const dc = get().demoCase;
      set(() => ({
        errorLog: dc?.request.input.error_log ?? DEMO_INPUT.errorLog,
        specExcerpt: dc?.request.input.spec_excerpt ?? DEMO_INPUT.specExcerpt,
      }));
    }

    try {
      let result: OrchestrationResponse;

      if (get().backendAvailable) {
        result = await api.orchestrateDemo(get().selectedModel ?? undefined);
      } else {
        await new Promise((r) => setTimeout(r, 1200 * 3.5));
        result = buildDemoResponse();
      }

      set(() => ({ result }));
      stagedReveal(set);
      setTimeout(() => set(() => ({ isRunning: false })), 1200 * 4 + 500);
    } catch (e) {
      try {
        await new Promise((r) => setTimeout(r, 2000));
        const result = buildDemoResponse();
        set(() => ({ result }));
        stagedReveal(set);
        setTimeout(() => set(() => ({ isRunning: false })), 1200 * 4 + 500);
      } catch {
        set(() => ({
          isRunning: false,
          error: e instanceof Error ? e.message : String(e),
          agentStatuses: [...INITIAL_STATUSES],
        }));
      }
    }
  },

  runCustom: async () => {
    const s = get();
    if (!s.backendAvailable) {
      set(() => ({ error: 'Backend not available. Start the server or use "Run Demo" for offline mode.' }));
      return;
    }
    const hasUploadedBundle = Boolean(
      s.errorLogFile && s.designImageFile && s.testedImageFile && s.specFiles.length > 0,
    );
    if (!hasUploadedBundle && !s.errorLog) {
      set(() => ({ error: 'Error log is required.' }));
      return;
    }
    if (!hasUploadedBundle && !s.specExcerpt) {
      set(() => ({ error: 'Spec excerpt (or at least one uploaded spec file) is required.' }));
      return;
    }

    set(() => ({
      isRunning: true, error: null, result: null,
      agentStatuses: ['running', 'idle', 'idle', 'idle', 'idle'] as AgentStatus[],
      revealedAgents: 1, currentAgentName: AGENT_NAMES[0],
      highlightedBoxLabel: null, highlightedSpecIdx: null, expandedAgentIdx: null,
      inputCollapsed: true,
    }));

    try {
      let result: OrchestrationResponse;
      if (hasUploadedBundle) {
        result = await api.orchestrateUploaded({
          input: {
            error_log_file: s.errorLogFile!,
            design_image_file: s.designImageFile!,
            tested_image_file: s.testedImageFile!,
            spec_files: s.specFiles,
            design_reference_files: s.designReferenceFiles,
          },
          options: { model: s.selectedModel ?? undefined, include_raw_agent_payloads: true },
        });
      } else {
        result = await api.orchestrate({
          input: {
            error_log: s.errorLog,
            spec_excerpt: s.specExcerpt || undefined,
            design_image: s.designImageFile
              ? { mime_type: s.designImageFile.mime_type, base64_data: s.designImageFile.base64_data }
              : s.designImageB64
                ? { mime_type: 'image/png', base64_data: s.designImageB64 }
                : { mime_type: 'image/png', file_path: 'data/assets/template_board.png' },
            tested_image: s.testedImageFile
              ? { mime_type: s.testedImageFile.mime_type, base64_data: s.testedImageFile.base64_data }
              : s.testedImageB64
                ? { mime_type: 'image/png', base64_data: s.testedImageB64 }
                : { mime_type: 'image/png', file_path: 'data/assets/tested_board.png' },
          },
          options: { model: s.selectedModel ?? undefined, include_raw_agent_payloads: true },
        });
      }
      set(() => ({ result }));
      stagedReveal(set);
      setTimeout(() => set(() => ({ isRunning: false })), 1200 * 4 + 500);
    } catch (e) {
      set(() => ({
        isRunning: false,
        error: e instanceof Error ? e.message : String(e),
        agentStatuses: [...INITIAL_STATUSES],
      }));
    }
  },

  reset: () => set(() => ({
    errorLog: '',
    specExcerpt: '',
    designImageB64: '',
    testedImageB64: '',
    errorLogFile: null,
    designImageFile: null,
    testedImageFile: null,
    specFiles: [],
    designReferenceFiles: [],
    isRunning: false,
    agentStatuses: [...INITIAL_STATUSES],
    revealedAgents: 0,
    currentAgentName: '',
    result: null,
    error: null,
    highlightedBoxLabel: null,
    highlightedSpecIdx: null,
    expandedAgentIdx: null,
    inputCollapsed: false,
  })),
}));
