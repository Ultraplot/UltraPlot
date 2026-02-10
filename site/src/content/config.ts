import { defineCollection, z } from "astro:content";

const docs = defineCollection({
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    order: z.number().optional(),
    source: z.string().optional(),
    draft: z.boolean().optional()
  })
});

export const collections = { docs };
