import { useState } from 'react';
import { useAuthStore } from '../store';
import { LogOut, Settings, Inbox, Users, MessageSquare } from 'lucide-react';
import keycloak from '../lib/keycloak';

export default function InboxPage() {
    const { user } = useAuthStore();
    const [activeView, setActiveView] = useState('inbox');

    const handleLogout = () => {
        keycloak.logout();
    };

    return (
        <div className="h-screen flex bg-gray-50">
            {/* Sidebar */}
            <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
                {/* Logo */}
                <div className="p-4 border-b border-gray-200">
                    <div className="flex items-center gap-2">
                        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                            <span className="text-white font-bold text-lg">M</span>
                        </div>
                        <div>
                            <h1 className="font-bold text-gray-900">MAX</h1>
                            <p className="text-xs text-gray-500">Inbox</p>
                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4">
                    <div className="space-y-1">
                        <button
                            onClick={() => setActiveView('inbox')}
                            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${activeView === 'inbox'
                                    ? 'bg-blue-50 text-blue-600'
                                    : 'text-gray-700 hover:bg-gray-50'
                                }`}
                        >
                            <Inbox className="w-5 h-5" />
                            <span className="font-medium">Inbox</span>
                            <span className="ml-auto bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                                12
                            </span>
                        </button>

                        <button
                            onClick={() => setActiveView('assigned')}
                            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${activeView === 'assigned'
                                    ? 'bg-blue-50 text-blue-600'
                                    : 'text-gray-700 hover:bg-gray-50'
                                }`}
                        >
                            <MessageSquare className="w-5 h-5" />
                            <span className="font-medium">Assigned to me</span>
                        </button>

                        <button
                            onClick={() => setActiveView('teams')}
                            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${activeView === 'teams'
                                    ? 'bg-blue-50 text-blue-600'
                                    : 'text-gray-700 hover:bg-gray-50'
                                }`}
                        >
                            <Users className="w-5 h-5" />
                            <span className="font-medium">Teams</span>
                        </button>
                    </div>
                </nav>

                {/* User Profile */}
                <div className="p-4 border-t border-gray-200">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                            <span className="text-blue-600 font-semibold text-sm">
                                {user?.full_name?.charAt(0) || 'U'}
                            </span>
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 truncate">
                                {user?.full_name || 'User'}
                            </p>
                            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                            onClick={() => setActiveView('settings')}
                        >
                            <Settings className="w-4 h-4" />
                            <span className="text-sm">Settings</span>
                        </button>
                        <button
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            onClick={handleLogout}
                        >
                            <LogOut className="w-4 h-4" />
                            <span className="text-sm">Logout</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col">
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Inbox className="w-8 h-8 text-gray-400" />
                        </div>
                        <h2 className="text-xl font-semibold text-gray-900 mb-2">
                            Welcome to MAX
                        </h2>
                        <p className="text-gray-600">
                            Your omnichannel inbox is ready. Select a conversation to start.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
