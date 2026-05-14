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

export interface ReportTestDetail {
  test_name: string;
  status: TestStatus;
  score: number;
  details: Record<string, unknown>;
  duration_ms: number;
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
  }>;
  warnings: Array<{
    category: string;
    test_name: string;
    score: number;
    details: Record<string, unknown>;
  }>;
  recommendations: string[];
  test_details: Record<string, ReportTestDetail[]>;
  certification_valid_until: string;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  warning_tests: number;
  skipped_tests: number;
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
}
