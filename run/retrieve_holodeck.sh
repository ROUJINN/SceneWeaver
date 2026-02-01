# Stop on errors
set -e

# Run the holodeck retrieval script
cd /home/lj/3D/SceneWeaver

lg holodeck

save_dir=$1
echo "Retrieving assets to: $save_dir"
python infinigen/assets/objaverse_assets/retrieve_holodeck.py ${save_dir}
