import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : '/api',
})

export const getFilters = () => api.get('/sales/filters').then(r => r.data)
export const getSummary = (params) => api.get('/sales/summary', { params }).then(r => r.data)
export const getMonthlyTrend = (params) => api.get('/sales/monthly', { params }).then(r => r.data)
export const getByBrand = (params) => api.get('/sales/by-brand', { params }).then(r => r.data)
export const getByChannel = (params) => api.get('/sales/by-channel', { params }).then(r => r.data)
export const getPurchaseMonthly = (params) => api.get('/purchase/monthly', { params }).then(r => r.data)
export const getPurchaseByBrand = (params) => api.get('/purchase/by-brand', { params }).then(r => r.data)
export const getSyncLogs = () => api.get('/sync/logs').then(r => r.data)
export const triggerEcountSync = () => api.post('/sync/ecount').then(r => r.data)
export const triggerGsheetsSync = () => api.post('/sync/gsheets').then(r => r.data)
