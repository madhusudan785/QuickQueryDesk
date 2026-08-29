/* Authentication service */

import api from './api';
import type { AuthResponse } from '../types';

export const authService = {
  async register(name: string, email: string, password: string, role: string): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/register', {
      name,
      email,
      password,
      role,
    });
    return response.data;
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login', {
      email,
      password,
    });
    return response.data;
  },
};
