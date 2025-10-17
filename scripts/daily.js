require('dotenv').config({ path: '.env.local' });
const Anthropic = require('@anthropic-ai/sdk');

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

async function generateArticle(topic) {
  console.log(`📝 Generating article about: ${topic}`);
  
  try {
    const message = await anthropic.messages.create({
      model: 'claude-3-haiku-20240307',
      max_tokens: 1500,
      messages: [{
        role: 'user',
        content: `Write a compelling 500-word article about "${topic}". 
                  Format with a catchy title, introduction, 3 main points, and conclusion.
                  Make it SEO-friendly and engaging.`
      }]
    });
    
    return message.content[0].text;
  } catch (error) {
    console.error('Error generating article:', error.message);
    return null;
  }
}

async function runDailyAutomation() {
  console.log('🚀 ORLA3 Daily Automation Starting...\n');
  
  // Today's topics (later we'll fetch trending topics)
  const topics = [
    'AI in Marketing 2025',
    'Content Automation Best Practices',
    'SEO for AI Search Engines'
  ];
  
  for (const topic of topics) {
    const article = await generateArticle(topic);
    if (article) {
      console.log(`✅ Article generated!\n`);
      console.log('---Preview---');
      console.log(article.substring(0, 200) + '...\n');
    }
  }
  
  console.log('🎉 Daily automation complete!');
}

runDailyAutomation();
