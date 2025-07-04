import argparse
import re
import sys
from collections import defaultdict
from file_extensions import FILE_EXTENSIONS

try:
	from tqdm import tqdm
	HAS_TQDM = True
except ImportError:
	HAS_TQDM = False


def parse_tree_line(line_num, raw_line):
	"""Parse a single line from tree output and return parsed item info."""
	# Find the position where the actual content begins
	content_start_index = 0
	for i, char in enumerate(raw_line):
		if char not in [' ', '\xa0', '│', '─', '└', '├', '┬', '┴', '┘', '┌', '┐', '┼']:
			content_start_index = i
			break
	
	# Determine level based on content_start_index (assuming 4 chars per level)
	current_indent_level = content_start_index // 4

	# Pattern to extract content after tree characters
	TREE_PREFIX_PATTERN = re.compile(r'^(?:[│─└├\s\xa0]*)(.*)$')
	
	# Extract the content using regex
	content_match = TREE_PREFIX_PATTERN.match(raw_line)
	if not content_match:
		return None
	
	# Clean the item name
	item_name_raw = content_match.group(1).strip()
	item_name_cleaned = re.sub(r'\s+', ' ', item_name_raw).strip()
	
	return {
		"line_num": line_num,
		"raw_line": raw_line,
		"indent_level": current_indent_level,
		"item_name": item_name_cleaned
	}

def is_file(item_name):
	"""Determine if an item is a file based on its extension."""
	# Remove size information (anything in parentheses at the end)
	clean_name = re.sub(r'\s*\([^)]*\)$', '', item_name)
	
	# Check if it has a file extension
	if '.' in clean_name:
		# Get the extension (everything after the last dot)
		extension = '.' + clean_name.split('.')[-1].lower()
		return extension in FILE_EXTENSIONS
	
	return False

def update_path(current_path, item, current_indent_level):
	"""Update the current path based on indentation level."""
	# Adjust current_path based on indentation level
	while len(current_path) > current_indent_level:
		current_path.pop()
	
	# Extend path if we're going deeper
	while len(current_path) < current_indent_level:
		current_path.append("")  # This shouldn't happen with proper tree structure
	
	# Set or add the current item at the appropriate level
	if len(current_path) == current_indent_level:
		current_path.append(item['item_name'])
	else:
		current_path[current_indent_level] = item['item_name']
	
	return "/".join(current_path)

def write_item_output(output_file, item):
	"""Write item output to file or console."""
	output_text = f"Line {item['line_num']} (Level {item['indent_level']}):\n"
	output_text += f"  Item Name: '{item['item_name']}'\n"
	output_text += f"  Full Path: '{item['full_path']}'\n"
	output_text += "-" * 20 + "\n"
	
	if output_file:
		output_file.write(output_text)
	else:
		print(output_text.rstrip())

def write_section_header(output_file, title):
	"""Write section header to file or console."""
	header = f"\n--- {title} ---\n"
	if output_file:
		output_file.write(header)
	else:
		print(header.rstrip())

def write_statistics(output_file, total_lines, files_count, extensions, files_only):
	"""Write final statistics to file or console."""
	stats_text = f"\n=== Final Statistics ===\n"
	stats_text += f"Total lines processed: {total_lines:,}\n"
	stats_text += f"Files found: {files_count:,}\n"
	
	if extensions and files_only:
		stats_text += f"\nFile types found:\n"
		for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
			stats_text += f"  .{ext}: {count:,} files\n"
	
	if output_file:
		output_file.write(stats_text)
	else:
		print(stats_text.rstrip())

def get_file_line_count(file_path):
	"""Get total line count for progress bar."""
	try:
		with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
			return sum(1 for _ in f)
	except:
		return None

def process_tree_file(file_path, files_only=False, progress_interval=50000, output_file_path=None, use_tqdm=None):
	"""Process tree file in streaming mode with progress display."""
	print(f"Processing file: {file_path}", file=sys.stderr)
	
	if output_file_path:
		print(f"Output will be written to: {output_file_path}", file=sys.stderr)
		output_file = open(output_file_path, 'w', encoding='utf-8')
	else:
		output_file = None
	
	# Determine if we should use tqdm
	if use_tqdm is None:
		use_tqdm = HAS_TQDM
	elif use_tqdm and not HAS_TQDM:
		print("Warning: tqdm not available, falling back to simple progress", file=sys.stderr)
		use_tqdm = False
	
	# Get file size for progress bar if using tqdm
	total_lines = None
	if use_tqdm:
		print("Counting lines for progress bar...", file=sys.stderr)
		total_lines = get_file_line_count(file_path)
		if total_lines:
			print(f"Total lines: {total_lines:,}", file=sys.stderr)
	
	try:
		section_title = "Files Only" if files_only else "All Items"
		write_section_header(output_file, section_title)
		
		current_path = []
		files_count = 0
		total_lines_processed = 0
		extensions = defaultdict(int)
		
		with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
			# Setup progress bar
			if use_tqdm and total_lines:
				progress_bar = tqdm(
					total=total_lines,
					desc="Processing",
					unit="lines",
					unit_scale=True,
					file=sys.stderr
				)
			else:
				progress_bar = None
			
			try:
				for raw_line in f:
					total_lines_processed += 1
					raw_line = raw_line.rstrip('\n\r')
					
					if not raw_line.strip():
						if progress_bar:
							progress_bar.update(1)
						continue
					
					item = parse_tree_line(total_lines_processed, raw_line)
					if not item:
						if progress_bar:
							progress_bar.update(1)
						continue
					
					# Update path
					full_path = update_path(current_path, item, item['indent_level'])
					item['full_path'] = full_path
					
					# Check if it's a file
					if is_file(item['item_name']):
						files_count += 1
						
						# Track extensions
						clean_name = re.sub(r'\s*\([^)]*\)$', '', item['item_name'])
						if '.' in clean_name:
							ext = clean_name.split('.')[-1].lower()
							extensions[ext] += 1
						
						# Output if files_only mode
						if files_only:
							write_item_output(output_file, item)
					elif not files_only:
						# Output all items if not files_only mode
						write_item_output(output_file, item)
					
					# Update progress
					if progress_bar:
						progress_bar.set_postfix({'Files': f"{files_count:,}"})
						progress_bar.update(1)
					elif total_lines_processed % progress_interval == 0:
						print(f"[Progress: {total_lines_processed:,} lines processed, {files_count:,} files found]", file=sys.stderr)
					
					# Flush output file periodically
					if output_file and total_lines_processed % 10000 == 0:
						output_file.flush()
			
			finally:
				if progress_bar:
					progress_bar.close()
	
	except KeyboardInterrupt:
		print(f"\nProcessing interrupted by user.", file=sys.stderr)
		print(f"Processed {total_lines_processed:,} lines, found {files_count:,} files.", file=sys.stderr)
	
	finally:
		# Final statistics
		write_statistics(output_file, total_lines_processed, files_count, extensions, files_only)
		
		if output_file:
			output_file.close()
			print(f"Output written to: {output_file_path}", file=sys.stderr)
		
		# Always show final stats on stderr for progress tracking
		print(f"\n=== Processing Complete ===", file=sys.stderr)
		print(f"Total lines processed: {total_lines_processed:,}", file=sys.stderr)
		print(f"Files found: {files_count:,}", file=sys.stderr)

def main():
	parser = argparse.ArgumentParser(description='Parse large tree output files efficiently')
	parser.add_argument('file_path', help='Path to the tree output file')
	parser.add_argument('--files-only', action='store_true', 
					   help='Show only files, not directories')
	parser.add_argument('--progress-interval', type=int, default=50000,
					   help='Show progress every N lines when not using tqdm (default: 50000)')
	parser.add_argument('--output-file', '-o', type=str,
					   help='Output file path (if not specified, output goes to console)')
	parser.add_argument('--no-tqdm', action='store_true',
					   help='Disable tqdm progress bar even if available')
	
	args = parser.parse_args()
	
	# Print configuration to stderr
	print(f"Files only: {args.files_only}", file=sys.stderr)
	if not args.no_tqdm and HAS_TQDM:
		print(f"Progress: Using tqdm progress bar", file=sys.stderr)
	else:
		print(f"Progress: Simple progress every {args.progress_interval:,} lines", file=sys.stderr)
	if args.output_file:
		print(f"Output file: {args.output_file}", file=sys.stderr)
	else:
		print(f"Output: Console", file=sys.stderr)
	print("-" * 50, file=sys.stderr)
	
	try:
		use_tqdm = not args.no_tqdm
		process_tree_file(args.file_path, args.files_only, args.progress_interval, args.output_file, use_tqdm)
	except FileNotFoundError:
		print(f"Error: File '{args.file_path}' not found.", file=sys.stderr)
	except Exception as e:
		print(f"Error processing file: {e}", file=sys.stderr)

if __name__ == "__main__":
	main()
