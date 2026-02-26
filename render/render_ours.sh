outdir="/home/lj/3D/SceneWeaver/fxxkingresults/renderings"
blend="/home/lj/3D/SceneWeaver/blender/blender"
script="/home/lj/3D/SceneWeaver/render/render_single_scene.py"

room="/home/lj/3D/SceneWeaver/fxxkingresults/Design_me_a_bedroom_0/"
blendfile="/home/lj/3D/SceneWeaver/fxxkingresults/Design_me_a_bedroom_0/record_files/scene_5.blend"

"$blend" "$blendfile" --background --python "$script" "$room"