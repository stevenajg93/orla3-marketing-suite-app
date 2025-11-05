import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY!,
});

// Platform configurations
const PLATFORMS = {
  linkedin: { maxLength: 3000, hashtagLimit: 5 },
  twitter: { maxLength: 280, threadMax: 10 },
  facebook: { maxLength: 63206 },
  instagram: { maxLength: 2200, hashtagLimit: 30 },
  youtube: { titleMax: 100, descriptionMax: 5000 },
  tiktok: { maxLength: 2200 },
  reddit: { titleMax: 300, selfTextMax: 40000 },
  pinterest: { maxLength: 500 },
  tumblr: { maxLength: 4096 },
  meta: { headlineMax: 40, primaryTextMax: 125 }
};

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { 
      action, // 'generate' | 'engage' | 'schedule' | 'analyze'
      articleContent, 
      articleTopic,
      platforms = ['all'],
      engagementType // 'comment' | 'reply' | 'follow' | 'monitor'
    } = body;

    // CONTENT GENERATION
    if (action === 'generate') {
      const socialPosts: Record<string, { content: string; platform: string; generated: string; scheduled: boolean }> = {};
      const requestedPlatforms = platforms[0] === 'all' ? Object.keys(PLATFORMS) : platforms;

      for (const platform of requestedPlatforms) {
        const prompt = getPlatformPrompt(platform, articleTopic, articleContent);
        const message = await anthropic.messages.create({
          model: 'claude-3-haiku-20240307',
          max_tokens: 1000,
          messages: [{ role: 'user', content: prompt }]
        });
        
        const firstBlock = message.content[0];
        const text = firstBlock.type === 'text' ? firstBlock.text : '';

        socialPosts[platform] = {
          content: text,
          platform,
          generated: new Date().toISOString(),
          scheduled: false
        };
      }

      return NextResponse.json({
        success: true,
        action: 'generate',
        posts: socialPosts
      });
    }

    // ENGAGEMENT AUTOMATION
    if (action === 'engage') {
      const engagements = await generateEngagements(engagementType);
      return NextResponse.json({
        success: true,
        action: 'engage',
        engagements
      });
    }

    // SCHEDULING
    if (action === 'schedule') {
      // Queue posts for optimal times per platform
      const schedule = generateOptimalSchedule(platforms);
      return NextResponse.json({
        success: true,
        action: 'schedule',
        schedule
      });
    }

    return NextResponse.json({ success: false, error: 'Invalid action' });

  } catch (error) {
    console.error('Social automation error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to process social action' },
      { status: 500 }
    );
  }
}

function getPlatformPrompt(platform: string, topic: string, content: string) {
  const prompts: Record<string, string> = {
    linkedin: `Create LinkedIn post about "${topic}":
              - Professional, value-focused
              - Include question for engagement
              - 3-5 hashtags
              - Mention ORLA3 naturally`,
    
    twitter: `Create Twitter/X thread about "${topic}":
             - 5-7 tweets max
             - Hook → Insights → CTA structure
             - Include relevant hashtags
             - Tag @ORLA3official`,
    
    facebook: `Create Facebook post about "${topic}":
              - Conversational tone
              - Include emoji
              - Ask for opinions
              - Link to ORLA3`,
    
    instagram: `Create Instagram caption about "${topic}":
               - Story-driven opening
               - Line breaks for readability
               - 10-15 hashtags at end
               - CTA to link in bio`,
    
    youtube: `Create YouTube description for "${topic}":
             - SEO-optimized title
             - Timestamps structure
             - Links to resources
             - Subscribe CTA`,
    
    tiktok: `Create TikTok caption about "${topic}":
            - Trendy, casual tone
            - Hook in first 3 words
            - Trending hashtags
            - Challenge or question`,
    
    reddit: `Create Reddit post about "${topic}":
            - Valuable, not promotional
            - Question or insight format
            - Subreddit-appropriate tone
            - No direct selling`,
    
    pinterest: `Create Pinterest description for "${topic}":
               - SEO keywords naturally included
               - Solution-focused
               - Save-worthy value
               - Link to full article`,
    
    tumblr: `Create Tumblr post about "${topic}":
            - Mix text with insights
            - Reblog-worthy format
            - Relevant tags
            - Community-focused`,
    
    meta: `Create Meta Ads copy for "${topic}":
          - Problem-agitate-solve structure
          - Clear value proposition
          - Strong CTA
          - A/B test variations`
  };
  
  return prompts[platform] + `\n\nContext: ${content?.substring(0, 1000)}`;
}

async function generateEngagements(type: string) {
  // This would connect to platform APIs to:
  // - Reply to comments on your posts
  // - Comment on relevant posts in your niche
  // - Follow strategic accounts
  // - Monitor brand mentions
  
  const message = await anthropic.messages.create({
    model: 'claude-3-haiku-20240307',
    max_tokens: 500,
    messages: [{
      role: 'user',
      content: `Generate 5 ${type} responses for ORLA3 social engagement:
                - Helpful and authentic
                - Add value, not just promote
                - Build relationships
                - Professional but friendly`
    }]
  });
  
  const firstBlock = message.content[0];
  const text = firstBlock.type === 'text' ? firstBlock.text : '';

  return {
    type,
    responses: text,
    generated: new Date().toISOString()
  };
}

function generateOptimalSchedule(platforms: string[]) {
  // Optimal posting times per platform (UTC)
  const optimal: Record<string, string[]> = {
    linkedin: ['08:00', '12:00', '17:00'],
    twitter: ['09:00', '13:00', '19:00', '22:00'],
    facebook: ['09:00', '15:00', '20:00'],
    instagram: ['11:00', '14:00', '19:00'],
    youtube: ['14:00', '17:00'],
    tiktok: ['06:00', '10:00', '17:00', '23:00'],
    reddit: ['08:00', '13:00', '17:00'],
    pinterest: ['20:00', '21:00'],
    tumblr: ['22:00', '23:00'],
    meta: ['12:00', '18:00']
  };
  
  const schedule: any = {};
  platforms.forEach(platform => {
    if (optimal[platform]) {
      schedule[platform] = optimal[platform];
    }
  });
  
  return schedule;
}
