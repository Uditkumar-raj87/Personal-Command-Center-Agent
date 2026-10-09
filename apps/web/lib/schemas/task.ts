import { z } from "zod";

export const taskSchema = z.object({
  title: z.string().min(1).max(240),
  description: z.string().optional(),
  deadline: z.string().optional(),
  estimated_minutes: z.coerce.number().int().min(15).max(180).default(30),
  energy_level: z.enum(["low", "medium", "high"]),
  priority_tag: z.enum(["urgent_important", "important", "routine", "low"]),
  source: z.enum(["manual_note", "web_form", "inbox"]).default("web_form"),
});

export type TaskInput = z.infer<typeof taskSchema>;