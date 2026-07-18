---
layout: page
permalink: /blog/
title: blog
nav: true
nav_order: 2
---

<div class="post">
  <div class="header-bar">
    <h1>blog</h1>
    <h2>Research notes, experiments, and lessons learned.</h2>
  </div>

  <ul class="post-list">
    {% for post in site.posts %}
      {% assign read_time = post.content | number_of_words | divided_by: 180 | plus: 1 %}
      {% if post.redirect %}
        {% assign post_href = post.redirect %}
      {% else %}
        {% assign post_href = post.url | relative_url %}
      {% endif %}
      <li>
        <h3>
          <a class="post-title" href="{{ post_href }}"{% if post.redirect %} target="_blank" rel="noopener noreferrer"{% endif %}>{{ post.title }}</a>
        </h3>
        <p>{{ post.description }}</p>
        <p class="post-meta">{{ read_time }} min read &nbsp; · &nbsp; {{ post.date | date: "%B %d, %Y" }}</p>
      </li>
    {% endfor %}
  </ul>
</div>
