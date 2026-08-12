export type AgentStatus = 'pending' | 'running' | 'completed' | 'failed';
export type TestStatus = 'pass' | 'fail' | 'warning' | 'skip';
export type CertificationLevel = 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE' | 'NOT_CERTIFIED';

export interface Agent {
  id: string;
  name: string;
  filename: string;
  language: string;
  file_size: number;
  status: AgentStatus;
  created_at: string;
  updated_at: string;
  overall_score: number | null;
  certification_level: CertificationLevel | null;
  test_count: number;
}

export interface TestResult {
  id: string;
  category: string;
  test_name: string;
  status: TestStatus;
  score: number;
  details: Record<string, unknown>;
  duration_ms: number;
  created_at?: string;
}

export interface AgentDetail extends Agent {
  test_results: TestResult[];
}

export interface CategoryResult {
  category: string;
  tests: TestResult[];
  average_score: number;
  passed: number;
  failed: number;
  warnings: number;
}

export interface TestResultsResponse {
  agent_id: string;
  status: AgentStatus;
  categories: CategoryResult[];
}

export interface AgentStatusResponse {
  agent_id: string;
  status: AgentStatus;
  completed_tests: number;
  total_tests: number;
  updated_at: string;
}

export interface CategoryScore {
  score: number;
  weight: number;
  passed: number;
  failed: number;
  warnings: number;
  skipped: number;
  total: number;
}

export interface StandardRef {
  code: string;
  framework: string;
  title: string;
  url: string;
}

export interface StandardCoverage extends StandardRef {
  status: TestStatus;
  score: number;
  passed: number;
  failed: number;
  warnings: number;
  skipped: number;
  total: number;
  tests: string[];
}

export interface FrameworkCoverage {
  framework: string;
  url: string;
  controls: number;
  passed: number;
  failed: number;
  warnings: number;
  score: number;
}

export interface ReportTestDetail {
  test_name: string;
  status: TestStatus;
  score: number;
  details: Record<string, unknown>;
  duration_ms: number;
  standards?: StandardRef[];
}

export interface AgenticFinding {
  id: string;
  title: string;
  status: TestStatus;
  score: number;
  message: string;
  evidence: string;
  standards: StandardRef[];
}

export interface Report {
  agent_id: string;
  agent_name: string;
  filename: string;
  language: string;
  file_size: number;
  test_date: string;
  overall_score: number;
  certification_level: CertificationLevel;
  category_scores: Record<string, CategoryScore>;
  critical_issues: Array<{
    category: string;
    test_name: string;
    score: number;
    details: Record<string, unknown>;
    standards?: StandardRef[];
  }>;
  warnings: Array<{
    category: string;
    test_name: string;
    score: number;
    details: Record<string, unknown>;
    standards?: StandardRef[];
  }>;
  recommendations: string[];
  test_details: Record<string, ReportTestDetail[]>;
  standards_coverage: StandardCoverage[];
  frameworks: FrameworkCoverage[];
  agentic_governance: AgenticFinding[];
  certification_valid_until: string;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  warning_tests: number;
  skipped_tests: number;
}

export interface PlatformStats {
  totals: {
    agents: number;
    tested: number;
    certified: number;
    not_certified: number;
    running: number;
    failed_runs: number;
    total_test_executions: number;
    pass_rate: number;
  };
  avg_score: number;
  score_distribution: Record<string, number>;
  certification_distribution: Record<CertificationLevel, number>;
  language_distribution: Record<string, number>;
  category_averages: Record<string, number>;
  category_pass_rates: Record<string, {
    passed: number; failed: number; warnings: number;
    total: number; pass_rate: number;
  }>;
  top_failures: Array<{ test: string; count: number }>;
  recent_agents: Array<{
    id: string; name: string; language: string; status: string;
    overall_score: number | null; certification_level: CertificationLevel | null;
    created_at: string;
  }>;
  top_agents: Array<{
    id: string; name: string; language: string;
    overall_score: number; certification_level: CertificationLevel;
  }>;
  test_summary: { passed: number; failed: number; warnings: number; total: number };
}

export interface Certificate {
  agent_id: string;
  agent_name: string;
  language: string;
  certification_level: CertificationLevel;
  overall_score: number;
  test_date: string;
  certification_valid_until: string;
  category_scores: Record<string, number>;
  issued_by: string;
  certificate_id: string;
  frameworks: FrameworkCoverage[];
}
