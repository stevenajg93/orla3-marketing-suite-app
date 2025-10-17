// WordPress REST API Integration for ORLA3
// Handles creating, updating, and managing posts

export class WordPressClient {
  private siteUrl: string;
  private username: string;
  private password: string;
  
  constructor() {
    this.siteUrl = process.env.WORDPRESS_SITE_URL || '';
    this.username = process.env.WORDPRESS_USERNAME || '';
    this.password = process.env.WORDPRESS_APP_PASSWORD || '';
  }

  // Create auth header for WordPress REST API
  private getAuthHeader(): string {
    const credentials = Buffer.from(`${this.username}:${this.password}`).toString('base64');
    return `Basic ${credentials}`;
  }

  // Create or update a post
  async publishPost(data: {
    title: string;
    content: string;
    slug?: string;
    excerpt?: string;
    categories?: number[];
    tags?: number[];
    status?: 'draft' | 'publish' | 'private';
  }) {
    try {
      const endpoint = `${this.siteUrl}/wp-json/wp/v2/posts`;
      
      // Check if post exists by slug
      if (data.slug) {
        const existing = await this.getPostBySlug(data.slug);
        if (existing) {
          // Update existing post
          return await this.updatePost(existing.id, data);
        }
      }

      // Create new post
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': this.getAuthHeader(),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: data.title,
          content: data.content,
          slug: data.slug,
          excerpt: data.excerpt,
          status: data.status || 'draft',
          categories: data.categories || [],
          tags: data.tags || []
        })
      });

      if (!response.ok) {
        throw new Error(`WordPress API error: ${response.status}`);
      }

      const post = await response.json();
      return {
        success: true,
        id: post.id,
        link: post.link,
        slug: post.slug
      };

    } catch (error) {
      console.error('WordPress publish error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  // Get post by slug
  async getPostBySlug(slug: string) {
    try {
      const endpoint = `${this.siteUrl}/wp-json/wp/v2/posts?slug=${slug}`;
      const response = await fetch(endpoint);
      
      if (!response.ok) return null;
      
      const posts = await response.json();
      return posts.length > 0 ? posts[0] : null;
      
    } catch (error) {
      console.error('WordPress fetch error:', error);
      return null;
    }
  }

  // Update existing post
  async updatePost(id: number, data: any) {
    try {
      const endpoint = `${this.siteUrl}/wp-json/wp/v2/posts/${id}`;
      
      const response = await fetch(endpoint, {
        method: 'PUT',
        headers: {
          'Authorization': this.getAuthHeader(),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: data.title,
          content: data.content,
          excerpt: data.excerpt,
          status: data.status || 'draft'
        })
      });

      if (!response.ok) {
        throw new Error(`WordPress update error: ${response.status}`);
      }

      const post = await response.json();
      return {
        success: true,
        id: post.id,
        link: post.link,
        slug: post.slug,
        updated: true
      };

    } catch (error) {
      console.error('WordPress update error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  // Schedule a post for future publishing
  async schedulePost(data: any, publishDate: Date) {
    return await this.publishPost({
      ...data,
      status: 'future',
      date: publishDate.toISOString()
    } as any);
  }

  // Get all posts
  async getPosts(params?: {
    per_page?: number;
    page?: number;
    status?: string;
  }) {
    try {
      const queryParams = new URLSearchParams({
        per_page: String(params?.per_page || 10),
        page: String(params?.page || 1),
        status: params?.status || 'publish'
      });

      const endpoint = `${this.siteUrl}/wp-json/wp/v2/posts?${queryParams}`;
      
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': this.getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error(`WordPress fetch error: ${response.status}`);
      }

      return await response.json();
      
    } catch (error) {
      console.error('WordPress fetch error:', error);
      return [];
    }
  }
}

// Export a singleton instance
export const wordpress = new WordPressClient();
