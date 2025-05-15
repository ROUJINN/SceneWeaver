conda activate layoutgpt
prompts=( "Design me a waiting room." "Design me a garage." "Design me a classroom.")
for p in "${prompts[@]}"; do
  for i in {0..1}; do
    python main.py "$p" "$i"
  done
done