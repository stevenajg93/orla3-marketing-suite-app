import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { saveArticles } from '@/lib/storage';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY!,
});

export async function POST() {
  try {
    console.log('Generating content via API...');
    
    const topics = [
      'ORLA3 Marketing Framework',
      'AI-Powered Content Strategy',
      'Automation for Small Businesses'
    ];
    
    const articles = [];
    
    for (const topic of topics) {
      const message = await anthropic.messages.create({
        model: 'claude-3-haiku-20240307',
        max_tokens: 1500,
        messages: [{
          role: 'user',
          content: `Write a compelling 500-word article about "${topic}". 
                    Format with a catchy title, introduction, 3 main points, and conclusion.
                    Make it SEO-friendly and engaging for business owners.`
        }]
      });
      
      const firstBlock = message.content[0];
      const text = firstBlock.type === 'text' ? firstBlock.text : '';

      articles.push({
        topic,
        content: text,
        generated: new Date().toISOString()
      });
    }
    
    // Save articles to storage
    saveArticles(articles);
    
    return NextResponse.json({ 
      success: true, 
      count: articles.length,
      articles 
    });
    
  } catch (error) {
    console.error('Generation error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to generate content' },
      { status: 500 }
    );
  }
}

export async function GET() {
  const { getArticles } = await import('@/lib/storage');
  const articles = getArticles();
  
  return NextResponse.json({ 
    success: true,
    count: articles.length,
    articles 
  });
}
