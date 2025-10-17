// Simple in-memory storage for articles
// In production, this would be a database

let storedArticles: any[] = [];

export function saveArticles(articles: any[]) {
  storedArticles = articles;
  return storedArticles;
}

export function getArticles() {
  return storedArticles;
}

export function addArticle(article: any) {
  storedArticles.push(article);
  return storedArticles;
}

export function clearArticles() {
  storedArticles = [];
  return storedArticles;
}
