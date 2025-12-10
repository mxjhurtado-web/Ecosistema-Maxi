'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Key, AlertCircle, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

interface APIKey {
    id: number;
    key_preview: string;
    status: string;
    last_used_at: string | null;
}

interface KeyStatus {
    total: number;
    active: number;
    exhausted: number;
    max_keys: number;
    keys: APIKey[];
}

export default function ApiKeyManager() {
    const [keys, setKeys] = useState<APIKey[]>([]);
    const [newKey, setNewKey] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState<KeyStatus>({
        total: 0,
        active: 0,
        exhausted: 0,
        max_keys: 4,
        keys: []
    });
    const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

    useEffect(() => {
        loadKeysStatus();
    }, []);

    const loadKeysStatus = async () => {
        try {
            const response = await fetch('/api/keys/status', {
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Failed to load keys');
            }

            const data = await response.json();
            setStatus(data);
            setKeys(data.keys);
        } catch (error) {
            console.error('Error loading keys:', error);
            showMessage('error', 'Error loading API keys');
        }
    };

    const showMessage = (type: 'success' | 'error' | 'info', text: string) => {
        setMessage({ type, text });
        setTimeout(() => setMessage(null), 5000);
    };

    const addKey = async () => {
        if (!newKey.trim()) {
            showMessage('error', 'Please enter an API key');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('/api/keys/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ api_key: newKey })
            });

            const data = await response.json();

            if (response.ok) {
                setNewKey('');
                await loadKeysStatus();
                showMessage('success', 'API key added successfully');
            } else {
                showMessage('error', data.detail || 'Failed to add API key');
            }
        } catch (error) {
            showMessage('error', 'Error adding API key');
        } finally {
            setLoading(false);
        }
    };

    const removeKey = async (keyId: number) => {
        if (!confirm('Are you sure you want to delete this API key?')) return;

        try {
            const response = await fetch(`/api/keys/${keyId}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            if (response.ok) {
                await loadKeysStatus();
                showMessage('success', 'API key removed successfully');
            } else {
                showMessage('error', 'Failed to remove API key');
            }
        } catch (error) {
            showMessage('error', 'Error removing API key');
        }
    };

    const resetKeys = async () => {
        if (!confirm('Reset all API keys to active status?')) return;

        setLoading(true);
        try {
            const response = await fetch('/api/keys/reset', {
                method: 'POST',
                credentials: 'include'
            });

            if (response.ok) {
                await loadKeysStatus();
                showMessage('success', 'All API keys reset to active');
            } else {
                showMessage('error', 'Failed to reset API keys');
            }
        } catch (error) {
            showMessage('error', 'Error resetting API keys');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto p-6">
            <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                        <Key className="w-6 h-6" />
                        Gemini API Keys
                    </h2>
                    <button
                        onClick={resetKeys}
                        disabled={loading || status.total === 0}
                        className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Reset All
                    </button>
                </div>

                {/* Message Banner */}
                {message && (
                    <div className={`mb-4 p-4 rounded-md flex items-center gap-2 ${message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
                            message.type === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
                                'bg-blue-50 text-blue-800 border border-blue-200'
                        }`}>
                        {message.type === 'success' && <CheckCircle className="w-5 h-5" />}
                        {message.type === 'error' && <XCircle className="w-5 h-5" />}
                        {message.type === 'info' && <AlertCircle className="w-5 h-5" />}
                        <span>{message.text}</span>
                    </div>
                )}

                {/* Status Indicators */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="text-sm text-green-600 font-medium">Active Keys</div>
                        <div className="text-3xl font-bold text-green-700">{status.active}</div>
                    </div>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <div className="text-sm text-yellow-600 font-medium">Exhausted</div>
                        <div className="text-3xl font-bold text-yellow-700">{status.exhausted}</div>
                    </div>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="text-sm text-blue-600 font-medium">Total / Max</div>
                        <div className="text-3xl font-bold text-blue-700">{status.total} / {status.max_keys}</div>
                    </div>
                </div>

                {/* Warning Alerts */}
                {status.active <= 1 && status.active > 0 && (
                    <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md flex items-start gap-2">
                        <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                        <div className="text-sm text-yellow-800">
                            <strong>Warning:</strong> Only {status.active} active key remaining. Consider adding more keys to avoid interruptions.
                        </div>
                    </div>
                )}

                {status.active === 0 && status.total > 0 && (
                    <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
                        <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                        <div className="text-sm text-red-800">
                            <strong>All keys exhausted!</strong> Keys will automatically reset tomorrow, or you can add new keys now.
                        </div>
                    </div>
                )}

                {/* Keys List */}
                <div className="space-y-3 mb-6">
                    <h3 className="text-lg font-semibold text-gray-700">Your API Keys</h3>
                    {keys.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <Key className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>No API keys added yet</p>
                            <p className="text-sm">Add your first Gemini API key below to start analyzing</p>
                        </div>
                    ) : (
                        keys.map((key) => (
                            <div
                                key={key.id}
                                className={`flex items-center justify-between p-4 rounded-lg border-2 ${key.status === 'active'
                                        ? 'bg-green-50 border-green-200'
                                        : 'bg-gray-50 border-gray-200'
                                    }`}
                            >
                                <div className="flex items-center gap-3 flex-1">
                                    <Key className={`w-5 h-5 ${key.status === 'active' ? 'text-green-600' : 'text-gray-400'
                                        }`} />
                                    <div className="flex-1">
                                        <div className="font-mono text-sm text-gray-700">{key.key_preview}</div>
                                        {key.last_used_at && (
                                            <div className="text-xs text-gray-500 mt-1">
                                                Last used: {new Date(key.last_used_at).toLocaleString()}
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${key.status === 'active'
                                            ? 'bg-green-100 text-green-700'
                                            : 'bg-gray-100 text-gray-600'
                                        }`}>
                                        {key.status === 'active' ? '✓ Active' : '⚠ Exhausted'}
                                    </span>
                                    <button
                                        onClick={() => removeKey(key.id)}
                                        className="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                                        title="Remove key"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Add New Key */}
                {status.total < status.max_keys && (
                    <div className="border-t pt-6">
                        <h3 className="text-lg font-semibold text-gray-700 mb-3">Add New API Key</h3>
                        <div className="flex gap-3">
                            <input
                                type="password"
                                value={newKey}
                                onChange={(e) => setNewKey(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && addKey()}
                                placeholder="Paste your Gemini API key here..."
                                disabled={loading}
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                            />
                            <button
                                onClick={addKey}
                                disabled={loading || !newKey.trim()}
                                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <Plus className="w-4 h-4" />
                                Add Key
                            </button>
                        </div>
                        <p className="text-sm text-gray-500 mt-2">
                            Get your API key from{' '}
                            <a
                                href="https://aistudio.google.com/app/apikey"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline"
                            >
                                Google AI Studio
                            </a>
                        </p>
                    </div>
                )}

                {status.total >= status.max_keys && (
                    <div className="border-t pt-6">
                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-800">
                            <strong>Maximum keys reached.</strong> You can have up to {status.max_keys} API keys. Remove an existing key to add a new one.
                        </div>
                    </div>
                )}
            </div>

            {/* Info Section */}
            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold text-blue-900 mb-2">How it works:</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Add up to 4 Gemini API keys for automatic rotation</li>
                    <li>• When one key reaches its quota, the system automatically switches to the next active key</li>
                    <li>• All keys reset to active status daily at midnight</li>
                    <li>• Your keys are encrypted and stored securely</li>
                </ul>
            </div>
        </div>
    );
}
