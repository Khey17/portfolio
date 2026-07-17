---
layout: page
title: projects
permalink: /projects/
description: Selected projects and research work.
nav: true
nav_order: 3
display_categories: [research]
horizontal: false
---

<div class="projects">
  {% for category in page.display_categories %}
    {% assign categorized_projects = site.projects | where: "category", category %}
    {% assign sorted_projects = categorized_projects | sort: "importance" %}
    <div class="row row-cols-1 row-cols-md-3">
      {% for project in sorted_projects %}
        {% include projects.liquid %}
      {% endfor %}
    </div>
  {% endfor %}
</div>
