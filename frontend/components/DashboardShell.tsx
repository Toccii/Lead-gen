"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { useRequireAuth } from "@/lib/auth-context";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/leads", label: "Lead" },
  { href: "/campaigns", label: "Campagne" },
  { href: "/logs", label: "Log" },
];

export default function DashboardShell({ children }: { children: ReactNode }) {
  const { email, logout, loading, token } = useRequireAuth();
  const pathname = usePathname();

  if (loading || !token) {
    return <div className="p-8 text-sm text-gray-500">Caricamento...</div>;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b px-6 py-4 flex items-center justify-between">
        <nav className="flex gap-5">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={
                pathname === item.href
                  ? "text-sm font-semibold"
                  : "text-sm text-gray-500 hover:text-black dark:hover:text-white"
              }
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <span>{email}</span>
          <button onClick={logout} className="underline">
            Esci
          </button>
        </div>
      </header>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
