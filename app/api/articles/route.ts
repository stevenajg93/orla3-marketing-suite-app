import { NextResponse } from 'next/server';
import { getArticles, addArticle } from '@/lib/storage';

export async function GET() {
  const articles = getArticles();
  return NextResponse.json(articles);
}

export async function POST(request: Request) {
  const body = await request.json();
  const newArticle = {
    id: Date.now(),
    topic: body.topic || body.title || 'Untitled Article',
    content: body.content || body.summary || '',
    generated: new Date().toISOString(),
    ...body
  };
  addArticle(newArticle);
  return NextResponse.json(newArticle);
}
