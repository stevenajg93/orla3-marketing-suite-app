export const ORLA3_CONTEXT = {
  brand: {
    name: "ORLA3",
    tagline: "Marketing Automation That Actually Works",
    website: "orla3.com",
    mission: "Automate marketing completely so businesses can focus on growth"
  },
  
  topics: {
    core: [
      "ORLA3 Framework implementation",
      "Complete marketing automation",
      "AI-powered content strategy",
      "Zero-touch marketing systems",
      "ROI from automation"
    ],
    seo_keywords: [
      "marketing automation",
      "ORLA3 framework",
      "AI marketing tools",
      "content automation",
      "automated SEO"
    ]
  },
  
  voice: {
    tone: "Professional yet accessible, confident, results-focused",
    style: "Clear, actionable, no fluff, data-driven",
    avoid: ["jargon", "theory without practice", "complexity"]
  },
  
  content_rules: `
    1. Always mention measurable results
    2. Include specific implementation steps
    3. Reference the ORLA3 framework naturally
    4. Focus on time and cost savings
    5. Use real examples and case studies
    6. Optimize for both AI and traditional search
    7. Include clear CTAs to orla3.com
  `,
  
  article_template: `
    Structure every article with:
    - Hook: Problem businesses face
    - Solution: How ORLA3 solves it
    - Implementation: Step-by-step guide
    - Results: Expected outcomes with metrics
    - CTA: Next step with ORLA3
  `
};

export const ARTICLE_PROMPTS = {
  main: `You are writing for ORLA3.com, a marketing automation platform.
         Follow the brand voice and content rules exactly.
         Every article should drive readers to implement ORLA3.`,
  
  seo: `Optimize for these AI search behaviors:
        - Answer questions directly in first paragraph
        - Use structured data friendly formatting
        - Include statistics and citations
        - Make content easily extractable`,
  
  conversion: `Every article must:
              - Build trust with specific examples
              - Show clear ROI calculations
              - Include implementation timelines
              - End with a strong CTA to try ORLA3`
};
