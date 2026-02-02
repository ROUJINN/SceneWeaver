import subprocess

cmd = """
lg infinigen
cd /home/lj/3D/SceneWeaver
python -m infinigen_examples.generate_indoors --seed 0 --save_dir /home/lj/3D/SceneWeaver/fxxkingresults/Design_me_a_bedroom_0 --task coarse --output_folder outputs/indoors/coarse_expand_whole_nobedframe -g fast_solve.gin overhead.gin studio.gin -p compose_indoors.terrain_enabled=False compose_indoors.invisible_room_ceilings_enabled=True > /home/lj/3D/SceneWeaver/test.log 2>&1
"""
subprocess.run(["bash", "-lic", cmd])
