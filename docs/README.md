# Access Amherst Backend Documentation Guide

This guide walks you through adding Documentation to Access Amherst with Sphinx.

## Prerequisites

Ensure you have the following installed in your project environment:

- Sphinx
- Django

You can install Sphinx with:

```bash
pip install sphinx
```

## Adding Documentation for Models

You can document your Django models (or other code) using Sphinx. Here’s an example using the `Event` model:

```python
# models.py
from django.db import models

class Event(models.Model):
    id = models.IntegerField(primary_key=True, unique=True, null=False, blank=False)
    title = models.CharField(max_length=255)
    author_name = models.CharField(max_length=255, null=True, blank=True)
    author_email = models.CharField(max_length=255, null=True, blank=True)
    pub_date = models.DateTimeField()
    host = models.TextField()
    link = models.URLField(max_length=500)
    picture_link = models.URLField(max_length=500, null=True, blank=True)
    event_description = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=500)
    categories = models.TextField()

    def __str__(self):
        return self.title
```

## Creating a `.rst` File for the Model

1. **Create an ********`.rst`******** file** in `docs/source/` for the model, e.g., `event_model.rst`:

   ```rst
   Event Model
   ============

   .. automodule:: access_amherst_backend.models
       :members: Event
   ```

2. **Update the ********`index.rst`******** file** to include the new `.rst` file:

   ```rst
   .. toctree::
       :maxdepth: 2
       :caption: Contents:

       event_model
   ```

3. **Rebuild the HTML documentation** by running:

   ```bash
   make html
   ```

## Viewing the Documentation

Each piece of documentation has it's own corresponding .html file that can be viewed:

- **Locally**: Navigate to `build/html/index.html` in your file system and open it in a browser.
- **In Gitpod**: Use the following command to preview it:
  ```bash
  gp preview $(pwd)/build/html/index.html
  ```
