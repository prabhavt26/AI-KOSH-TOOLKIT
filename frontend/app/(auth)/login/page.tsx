"use client"

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLogin } from "../../../hooks/use-auth";
import { useAuthStore } from "../../../stores/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Database, LogIn } from "lucide-react";
import { useEffect } from "react";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address."),
  password: z.string().min(8, "Password must be at least 8 characters long."),
});

type LoginValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { mutate: login, isPending, error } = useLogin();
  const { user, loading, fetchUser } = useAuthStore();

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard");
    }
  }, [user, loading, router]);

  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = (data: LoginValues) => {
    login(data, {
      onSuccess: () => {
        router.push("/upload");
      },
    });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-transparent px-4 animate-fade-in">
      <div className="relative w-full max-w-md">
        {/* Subtle decorative glow overlays consistent with portal style */}
        <div className="absolute -top-16 -left-16 h-48 w-48 rounded-full bg-primary/10 blur-3xl"></div>
        <div className="absolute -bottom-16 -right-16 h-48 w-48 rounded-full bg-accent/5 blur-3xl"></div>

        <Card className="border border-border/40 bg-card shadow-lg backdrop-blur-xl">
          <CardHeader className="space-y-2 text-center pb-4">
            <div className="flex justify-center mb-2">
              <Link href="/" className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 text-primary transition hover:opacity-90">
                <Database className="h-6 w-6 text-accent" />
              </Link>
            </div>
            <CardTitle className="text-3xl font-serif font-black tracking-tight text-primary">
              Welcome Back
            </CardTitle>
            <CardDescription className="text-muted-foreground text-xs font-semibold">
              Sign in to assess and score your health research datasets.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3 text-xs font-semibold text-rose-600 dark:text-rose-400">
                {error.message || "Invalid email or password. Please try again."}
              </div>
            )}

            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem className="space-y-1.5">
                      <FormLabel className="text-foreground text-xs font-bold uppercase tracking-wider">Email Address</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="name@example.com"
                          className="border-border/40 bg-white/70 text-foreground placeholder-muted-foreground/60 focus-visible:ring-primary text-xs font-medium"
                          disabled={isPending}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage className="text-rose-500 font-semibold text-[11px]" />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem className="space-y-1.5">
                      <div className="flex justify-between items-center">
                        <FormLabel className="text-foreground text-xs font-bold uppercase tracking-wider">Password</FormLabel>
                      </div>
                      <FormControl>
                        <Input
                          type="password"
                          placeholder="••••••••"
                          className="border-border/40 bg-white/70 text-foreground placeholder-muted-foreground/60 focus-visible:ring-primary text-xs font-medium"
                          disabled={isPending}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage className="text-rose-500 font-semibold text-[11px]" />
                    </FormItem>
                  )}
                />

                <Button
                  type="submit"
                  className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-bold transition py-5 mt-2"
                  disabled={isPending}
                >
                  {isPending ? (
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent mr-2"></div>
                  ) : (
                    <LogIn className="h-4 w-4 mr-2" />
                  )}
                  Sign In
                </Button>
              </form>
            </Form>
          </CardContent>
          <CardFooter className="flex justify-center border-t border-border/30 pt-4 pb-6">
            <span className="text-xs text-muted-foreground font-medium">
              Don&apos;t have an account?{" "}
              <Link href="/register" className="font-bold text-accent hover:underline">
                Create one
              </Link>
            </span>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
