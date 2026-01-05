import { create } from 'zustand';

/**
 * Global auth store
 */
export const useAuthStore = create((set) => ({
    user: null,
    isAuthenticated: false,
    isLoading: true,

    setUser: (user) => set({ user, isAuthenticated: true, isLoading: false }),
    clearUser: () => set({ user: null, isAuthenticated: false, isLoading: false }),
    setLoading: (isLoading) => set({ isLoading }),
}));

/**
 * Conversations store
 */
export const useConversationsStore = create((set) => ({
    conversations: [],
    selectedConversation: null,
    filter: 'all',
    searchQuery: '',

    setConversations: (conversations) => set({ conversations }),
    setSelectedConversation: (conversation) => set({ selectedConversation: conversation }),
    setFilter: (filter) => set({ filter }),
    setSearchQuery: (searchQuery) => set({ searchQuery }),

    addConversation: (conversation) => set((state) => ({
        conversations: [conversation, ...state.conversations]
    })),

    updateConversation: (id, updates) => set((state) => ({
        conversations: state.conversations.map(conv =>
            conv.id === id ? { ...conv, ...updates } : conv
        )
    })),
}));
