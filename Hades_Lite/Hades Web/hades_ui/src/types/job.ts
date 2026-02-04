/**
 * Job types
 */

export enum JobStatus {
    QUEUED = 'queued',
    PROCESSING = 'processing',
    COMPLETED = 'completed',
    FAILED = 'failed',
}

export enum SemaforoLevel {
    VERDE = 'verde',
    AMARILLO = 'amarillo',
    ROJO = 'rojo',
}

export interface DateInfo {
    original: string;
    display: string;
    format: string;
    is_valid: boolean;
    is_ambiguous?: boolean;
    is_expired?: boolean;
    days_until_expiry?: number;
    warnings?: string[];
}

export interface Country {
    code: string;
    name: string;
}

export interface ExtractedData {
    name: string | null;
    id_number: string | null;
    id_type: string | null;
}

export interface ForensicResult {
    score: number;
    semaforo: SemaforoLevel;
    security_elements: string;
    print_quality: string;
    manipulation_detected: boolean;
    warnings: string[];
}

export interface AnalysisResult {
    ocr_text: string;
    ocr_text_translated?: string;
    language_detected: string;
    was_translated: boolean;
    country: Country;
    dates: Record<string, DateInfo>;
    extracted_data: ExtractedData;
    forensics: ForensicResult;
    semaforo: SemaforoLevel;
    score: number;
    warnings: string[];
    metadata: Record<string, any>;
}

export interface Job {
    id: string;
    user_id: string;
    user_email?: string;
    user_name?: string;
    status: JobStatus;
    result?: AnalysisResult;
    exported_to_drive: boolean;
    drive_file_id?: string;
    drive_url?: string;
    country_detected?: string;
    semaforo?: SemaforoLevel;
    score?: number;
    name_extracted?: string;
    id_number_extracted?: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
    celery_task_id?: string;
}

export interface JobListItem {
    id: string;
    status: JobStatus;
    country_detected?: string;
    semaforo?: SemaforoLevel;
    score?: number;
    created_at: string;
    completed_at?: string;
}

export interface JobFilters {
    country?: string;
    semaforo?: SemaforoLevel;
    skip?: number;
    limit?: number;
}
