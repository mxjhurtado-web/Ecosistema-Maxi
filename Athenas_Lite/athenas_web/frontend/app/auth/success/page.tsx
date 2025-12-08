"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function AuthSuccessPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const role = searchParams.get("role");

    useEffect(() => {
        // Redirect based on role
        if (role === "admin") {
            router.push("/admin");
        } else {
            router.push("/dashboard");
        }
    }, [role, router]);

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg
                        className="w-8 h-8 text-green-600"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                        />
                    </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    ¡Autenticación exitosa!
                </h2>
                <p className="text-gray-600">Redirigiendo...</p>
            </div>
        </div>
    );
}
