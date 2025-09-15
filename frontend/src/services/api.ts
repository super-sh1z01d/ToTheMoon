import axios from 'axios';

export interface Pool {
    id: number;
    pool_address: string;
    dex_name: string;
}

// This should match the backend SQLModel for Token
export interface Token {
    id: number;
    token_address: string;
    name: string | null;
    status: string;
    created_at: string; // ISO format string
    activated_at?: string; // ISO format string
    last_score_value?: number;
    last_smoothed_score?: number;
    last_updated: string; // ISO format string
    pools?: Pool[];
}

// This should match the backend SQLModel for ScoringParameter
export interface ScoringParameter {
    id: number;
    param_name: string;
    param_value: number;
    is_active: boolean;
}

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
});

export const fetchTokens = async (): Promise<Token[]> => {
    try {
        const response = await apiClient.get<Token[]>('/tokens');
        return response.data;
    } catch (error) {
        console.error("Error fetching tokens:", error);
        return [];
    }
};

export const fetchParameters = async (): Promise<ScoringParameter[]> => {
    try {
        const response = await apiClient.get<ScoringParameter[]>('/parameters');
        return response.data;
    } catch (error) {
        console.error("Error fetching parameters:", error);
        return [];
    }
};

export const updateParameters = async (params: ScoringParameter[]): Promise<ScoringParameter[]> => {
    try {
        const response = await apiClient.post<ScoringParameter[]>('/parameters', params);
        return response.data;
    } catch (error) {
        console.error("Error updating parameters:", error);
        return [];
    }
};
