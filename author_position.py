import csv

def process_csv_with_author_position(csv_file, search_column, search_string, authorships_column, output_file):
    """
    Search for a string in a CSV column, count pipes before it, save as 'author position',
    and extract the corresponding phrase from another column after the same number of pipes.
    
    Args:
        csv_file: Path to the CSV file
        search_column: Name of the column to search in
        search_string: String to search for
        authorships_column: Name of the column to extract phrases from
        output_file: Path to save the output CSV
    """
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Add new columns
        new_headers = list(headers) + ['author position', 'extracted_author']
        
        output_rows = []
        
        for row in reader:
            # Get the cell content from the search column
            search_cell = row.get(search_column, '')
            authorships_cell = row.get(authorships_column, '')
            
            author_position = ''
            extracted_author = ''
            
            if search_string in search_cell:
                # Find the position of the search string
                position = search_cell.find(search_string)
                
                # Count | characters before this position
                text_before = search_cell[:position]
                pipe_count = text_before.count('|')
                
                author_position = pipe_count
                
                # Now find the phrase after the same number of pipes in authorships column
                if authorships_cell:
                    parts = authorships_cell.split('|')
                    if pipe_count < len(parts):
                        extracted_author = parts[pipe_count].strip()
            
            # Add new data to row
            row['author position'] = author_position
            row['extracted_author'] = extracted_author
            output_rows.append(row)
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_headers)
        writer.writeheader()
        writer.writerows(output_rows)
    
    print(f"Processing complete. Output saved to {output_file}")
    print(f"Added columns: 'author position' and 'extracted_author'")

# Usage example
if __name__ == "__main__":
    csv_file = "your_file.csv"
    search_column = "Column_Name_To_Search"  # e.g., "Affiliations"
    search_string = "your_search_term"  # e.g., "University of Chicago"
    authorships_column = "Authorships"
    output_file = "output_with_author_position.csv"
    
    process_csv_with_author_position(
        csv_file, 
        search_column, 
        search_string, 
        authorships_column, 
        output_file
    )
