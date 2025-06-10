#!/bin/bash
# analyze_single.sh
# Usage: ./analyze_single.sh /path/to/project /path/to/final_output.json

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 /path/to/project /path/to/final_output.json"
  exit 1
fi

project="$1"
final_output="$2"

# Create temporary files for the two pipelines
temp_commits=$(mktemp)
temp_stats=$(mktemp)

cd "$project" || { echo "Failed to cd into $project"; exit 1; }

# Get total number of commits
total_commits=$(git rev-list --count HEAD)
echo "Found $total_commits commits to process"

echo "Processing commit data (Pipeline 1)..."
# --- Pipeline 1: Git log for commit data ---
git log \
  --pretty=format:'%n{%n  "commit": "%H",%n  "author": "%an <%ae>",%n  "date": "%ad",%n  "message": "%f":FILES:' \
  | \
perl -ne '
  BEGIN{
    print "[";
    $total = '${total_commits}';
    $count = 0;
  }
  if ($i = (/:FILES:[\n\r]*$/../^$/)) {
    if ($i == 1) {
      s/:FILES:[\n\r]*$//;
      $message = $_;
      $count++;
      printf STDERR "\rProcessing commits: %d/%d (%.1f%%)", $count, $total, ($count/$total*100);
    } elsif ($i =~ /E0$/) {
      print_files();
      @files = ();
    } elsif ($_ !~ /^$/) {
      chomp $_;
      push @files, $_;
    }
  } else { print; }
  END { 
    print_files(1);
    printf STDERR "\nCompleted processing %d commits\n", $count;
  }
  sub print_files {
    $last_line = shift;
    print $message;
    @files ?
      print qq(,\n  "files": [\n@{[join qq(,\n), map {qq(    "$_")} map {json_escape($_)} @files]}\n  ]\n})
      : print "\n}";
    $last_line ? print "]" : print @files ? "," : ",\n";
  };
  sub json_escape { $_ = shift; s/([\\"])/\\\1/g; return $_; }' \
> "$temp_commits"

echo "Processing stats data (Pipeline 2)..."
# --- Pipeline 2: Git log for stats ---
git log \
  --numstat \
  --format='%H' \
  | \
perl -lawne '
      BEGIN {
        $total = '${total_commits}';
        $count = 0;
      }
      if (defined $F[1]) {
          print qq#{"insertions": "$F[0]", "deletions": "$F[1]", "path": "$F[2]"},#
      } elsif (defined $F[0]) {
          $count++;
          printf STDERR "\rProcessing commit stats: %d/%d (%.1f%%)", $count, $total, ($count/$total*100);
          print qq#],\n"$F[0]": [#
      };
      END{
        print qq#],#;
        printf STDERR "\nCompleted processing %d commit stats\n", $count;
      }' | \
tail -n +2 | \
perl -wpe 'BEGIN{print "{"}; END{print "}"}' | \
tr "\n" " " | \
perl -wpe 's#(]|}),\s*(]|})#$1$2#g' | \
perl -wpe 's#,\s*?}$#}#' \
> "$temp_stats"

echo "Merging data into final JSON file..."
# --- Merge the two outputs into one final JSON object ---
echo "{" > "$final_output"
echo '"commits": ' >> "$final_output"
cat "$temp_commits" >> "$final_output"
echo ',' >> "$final_output"
echo '"stats": ' >> "$final_output"
cat "$temp_stats" >> "$final_output"
echo "}" >> "$final_output"

rm "$temp_commits" "$temp_stats"

echo "Analysis complete! Output saved to: $final_output" 