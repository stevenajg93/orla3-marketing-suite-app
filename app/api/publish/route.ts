import { NextResponse } from 'next/server';
import { wordpress } from '@/lib/wordpress';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { 
      title, 
      content, 
      slug,
      excerpt,
      status = 'draft',
      action = 'create' // 'create' | 'update' | 'schedule'
    } = body;

    // Validate required fields
    if (!title || !content) {
      return NextResponse.json(
        { success: false, error: 'Title and content are required' },
        { status: 400 }
      );
    }

    let result;

    // Generate slug if not provided
    const postSlug = slug || title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');

    // Create excerpt if not provided
    const postExcerpt = excerpt || content
      .replace(/<[^>]*>/g, '') // Remove HTML
      .substring(0, 150) + '...';

    if (action === 'schedule' && body.publishDate) {
      // Schedule for future
      result = await wordpress.schedulePost({
        title,
        content,
        slug: postSlug,
        excerpt: postExcerpt,
        status: 'future'
      }, new Date(body.publishDate));
    } else {
      // Create or update immediately
      result = await wordpress.publishPost({
        title,
        content,
        slug: postSlug,
        excerpt: postExcerpt,
        status
      });
    }

    if (result.success) {
      return NextResponse.json({
        success: true,
        message: result.updated ? 'Post updated' : 'Post created',
        post: {
          id: result.id,
          link: result.link,
          slug: result.slug
        }
      });
    } else {
      return NextResponse.json(
        { success: false, error: result.error },
        { status: 500 }
      );
    }

  } catch (error) {
    console.error('Publish API error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to publish to WordPress' },
      { status: 500 }
    );
  }
}

// GET endpoint to check WordPress connection
export async function GET() {
  try {
    const posts = await wordpress.getPosts({ per_page: 5 });
    
    return NextResponse.json({
      success: true,
      connected: posts.length >= 0,
      recentPosts: posts.length,
      message: posts.length > 0 
        ? `Connected! Found ${posts.length} recent posts`
        : 'Connected but no posts found'
    });
    
  } catch (error) {
    return NextResponse.json({
      success: false,
      connected: false,
      error: 'Cannot connect to WordPress'
    });
  }
}
