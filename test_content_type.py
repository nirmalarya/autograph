#!/usr/bin/env python3
content_type = 'text/csv; charset=utf-8'
print('Testing content-type check:')
print(f'content_type = "{content_type}"')
print(f'startswith("text/csv") = {content_type.startswith("text/csv")}')
print(f'startswith tuple = {content_type.startswith(("image/", "application/pdf", "application/octet-stream", "text/csv"))}')
