"use client"

import React, { useState } from "react";
import Link from "next/link";
import { useAuthStore } from "../stores/auth";
import { Button } from "@/components/ui/button";
import { useRouter, usePathname } from "next/navigation";
import { 
  ShieldCheck, LogOut, Upload, LayoutDashboard, Database, 
  Menu, X, FileText, CheckCircle
} from "lucide-react";

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  if (!user) return null;

  const mainLinks = [
    { href: "/upload", label: "Upload Wizard", icon: Upload },
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  ];

  const specLinks = [
    { href: "/lite-version", label: "Lite Spec" },
    { href: "/technical-version", label: "Technical Spec" },
  ];

  const isActive = (path: string) => {
    if (path === "/dashboard") return pathname.startsWith("/dashboard");
    return pathname === path;
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-md">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 max-w-7xl">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2 font-bold text-primary transition hover:opacity-90 shrink-0">
          <Database className="h-5 w-5 text-accent" />
          <span className="tracking-wide font-serif text-lg">
            MIDAS <span className="text-accent">2.0 TOOLKIT</span>
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center gap-6">
          {mainLinks.map((link) => {
            const Icon = link.icon;
            const active = isActive(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-1.5 text-sm font-semibold transition-colors ${
                  active ? "text-accent border-b-2 border-accent py-5 -mb-0.5" : "text-muted-foreground hover:text-primary py-5"
                }`}
              >
                <Icon className="h-4 w-4" />
                {link.label}
              </Link>
            );
          })}

          <div className="h-4 w-[1px] bg-border" />

          {/* Reference Docs Menu */}
          <div className="flex items-center gap-4">
            {specLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`text-xs font-bold uppercase tracking-wider transition-colors ${
                  isActive(link.href) ? "text-accent" : "text-muted-foreground hover:text-primary"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {user.role === "admin" && (
            <>
              <div className="h-4 w-[1px] bg-border" />
              <Link
                href="/admin"
                className={`flex items-center gap-1.5 text-sm font-semibold transition-colors ${
                  isActive("/admin") ? "text-rose-500 border-b-2 border-rose-500 py-5 -mb-0.5" : "text-muted-foreground hover:text-rose-500 py-5"
                }`}
              >
                <ShieldCheck className="h-4 w-4" />
                Admin Console
              </Link>
            </>
          )}
        </nav>

        {/* User details & logout */}
        <div className="hidden lg:flex items-center gap-4">
          <div className="text-right">
            <div className="text-xs font-semibold text-foreground">{user.email}</div>
            <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{user.role}</div>
          </div>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={handleLogout}
            className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg h-9 w-9"
            title="Log Out"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>

        {/* Mobile menu trigger */}
        <div className="flex lg:hidden items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="text-foreground hover:bg-muted"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {/* Mobile Menu Panel */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-border/40 bg-background/95 backdrop-blur-md px-4 py-4 space-y-4 animate-slide-in">
          <div className="space-y-1.5">
            <div className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground px-2">Navigation</div>
            {mainLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-2.5 p-2 rounded-md text-sm font-semibold ${
                  isActive(link.href) ? "bg-accent/10 text-accent" : "text-muted-foreground hover:bg-muted"
                }`}
              >
                <link.icon className="h-4 w-4" />
                {link.label}
              </Link>
            ))}
          </div>

          <div className="border-t border-border/40 pt-3 space-y-1.5">
            <div className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground px-2">MIDAS Spec References</div>
            {specLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-2 p-2 rounded-md text-sm font-medium ${
                  isActive(link.href) ? "bg-accent/10 text-accent" : "text-muted-foreground hover:bg-muted"
                }`}
              >
                <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                {link.label}
              </Link>
            ))}
          </div>

          {user.role === "admin" && (
            <div className="border-t border-border/40 pt-3">
              <Link
                href="/admin"
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-2.5 p-2 rounded-md text-sm font-semibold ${
                  isActive("/admin") ? "bg-rose-500/10 text-rose-500" : "text-muted-foreground hover:bg-muted"
                }`}
              >
                <ShieldCheck className="h-4 w-4" />
                Admin Console
              </Link>
            </div>
          )}

          <div className="border-t border-border/40 pt-4 flex items-center justify-between px-2">
            <div>
              <div className="text-xs font-semibold text-foreground">{user.email}</div>
              <div className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest">{user.role}</div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="border-destructive/30 hover:bg-destructive/10 text-destructive text-xs gap-1"
            >
              <LogOut className="h-3.5 w-3.5" /> Log Out
            </Button>
          </div>
        </div>
      )}
    </header>
  );
}
