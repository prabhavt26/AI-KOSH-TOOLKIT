"use client"

import React from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { User } from "@/lib/types";
import { useAuthStore } from "@/stores/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Users, Calendar, Power, AlertOctagon } from "lucide-react";

export default function AdminPage() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuthStore();

  // Role Guard
  const isAdmin = currentUser?.role === "admin";

  const { data: users = [], isLoading, error } = useQuery<User[]>({
    queryKey: ["admin-users"],
    queryFn: () => api.get<User[]>("/api/v1/admin/users"),
    enabled: isAdmin, // Only fetch if user is admin
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (userId: string) => api.post<User>(`/api/v1/admin/users/${userId}/toggle-active`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  const handleToggleActive = async (userId: string) => {
    try {
      await toggleActiveMutation.mutateAsync(userId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update user status.";
      alert(msg);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  if (!isAdmin) {
    return (
      <div className="max-w-md mx-auto pt-16">
        <Card className="border border-red-500/20 bg-red-500/5 p-6 text-center space-y-4 shadow-lg">
          <AlertOctagon className="h-12 w-12 text-rose-600 mx-auto" />
          <CardTitle className="text-xl font-serif font-bold text-foreground">Access Denied</CardTitle>
          <CardDescription className="text-sm text-muted-foreground">
            This administrator console is restricted to users with the administrator role only.
          </CardDescription>
          <Link href="/dashboard" passHref className="block mt-4">
            <Button variant="outline" className="border-border hover:bg-muted text-xs">
              <ArrowLeft className="h-4 w-4 mr-1.5" /> Return to Dashboard
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-border pb-4">
        <Users className="h-7 w-7 text-accent" />
        <div>
          <h1 className="text-3xl font-serif font-black tracking-tight text-primary">Administrator Console</h1>
          <p className="text-xs text-muted-foreground mt-0.5 font-medium">
            Manage user accounts, toggle active states, and monitor system enrollment.
          </p>
        </div>
      </div>

      {/* Users Card List */}
      <Card className="bg-card border border-border shadow-md">
        <CardHeader className="pb-4">
          <CardTitle className="text-sm font-bold text-foreground">Registered Users</CardTitle>
          <CardDescription className="text-xs text-muted-foreground font-medium">
            Administrators cannot read datasets or quality reports due to strict security guidelines.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-36 flex-col items-center justify-center gap-2">
              <div className="h-6 w-6 animate-spin rounded-full border border-primary border-t-transparent"></div>
              <span className="text-xs text-muted-foreground font-medium">Loading user catalog...</span>
            </div>
          ) : error ? (
            <p className="text-xs text-rose-600 text-center py-4 font-semibold">Failed to fetch users: {error.message}</p>
          ) : users.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-4 font-medium">No users enrolled in system.</p>
          ) : (
            <div className="rounded-lg border border-border overflow-hidden bg-background/50">
              <Table>
                <TableHeader className="bg-muted/40">
                  <TableRow className="border-b border-border">
                    <TableHead className="font-bold text-foreground text-xs uppercase tracking-wider">Email Address</TableHead>
                    <TableHead className="font-bold text-foreground text-xs uppercase tracking-wider">Role</TableHead>
                    <TableHead className="font-bold text-foreground text-xs uppercase tracking-wider">Joined</TableHead>
                    <TableHead className="font-bold text-foreground text-xs uppercase tracking-wider">Status</TableHead>
                    <TableHead className="w-[100px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((u) => {
                    const isSelf = u.id === currentUser?.id;
                    return (
                      <TableRow key={u.id} className="border-b border-border/50 hover:bg-muted/50 transition-colors">
                        <TableCell className="font-semibold text-foreground text-xs">{u.email}</TableCell>
                        <TableCell>
                          <Badge className={`text-[9px] font-bold rounded uppercase ${
                            u.role === "admin" 
                              ? "bg-purple-500/10 text-purple-600 border border-purple-500/20"
                              : u.role === "reviewer"
                              ? "bg-sky-500/10 text-sky-600 border border-sky-500/20"
                              : "bg-slate-500/10 text-slate-600 border border-slate-500/20"
                          }`}>
                            {u.role}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground font-medium">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                            {formatDate(u.created_at)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge className={`text-[9px] font-bold rounded uppercase ${
                            u.is_active
                              ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20"
                              : "bg-rose-500/10 text-rose-600 border border-rose-500/20"
                          }`}>
                            {u.is_active ? "Active" : "Suspended"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {!isSelf && (
                            <Button
                              size="sm"
                              variant={u.is_active ? "destructive" : "default"}
                              onClick={() => handleToggleActive(u.id)}
                              disabled={toggleActiveMutation.isPending}
                              className={`text-[10px] font-bold h-7 px-2.5 ${
                                u.is_active
                                  ? "bg-rose-500/10 text-rose-600 hover:bg-rose-500/20 border border-rose-500/20"
                                  : "bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20 border border-emerald-500/20"
                              }`}
                            >
                              <Power className="mr-1 h-3.5 w-3.5" />
                              {u.is_active ? "Suspend" : "Activate"}
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
