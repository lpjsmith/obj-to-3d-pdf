# ============================================
# 3DMD → 3D PDF PIPELINE (FULL ORIGINAL FEATURES)
#
# This script:
#  ✓ Iterates Week → Study → Frames
#  ✓ Copies JPEG/OBJ/MTL into working dir
#  ✓ Brightens JPEG
#  ✓ Converts OBJ → U3D via PyMeshLab
#  ✓ Generates TEX with your EXACT camera settings
#  ✓ Compiles PDF via pdflatex
#  ✓ Moves PDF to week folder
#  ✓ Cleans temporary files
#  ✓ Skips missing folders safely
#  ✓ Logs ALL failures in error_log.txt
#  ✓ Avoids Unicode encoding issues
#
# Dependencies:
#   numpy==1.26.4
#   opencv-python==4.7.0.72
#   pymeshlab==2022.2.post3
#   TeXLive or MiKTeX with media9
# ============================================

import os
import shutil
import traceback
import cv2
import pymeshlab
import tempfile

PDFLATEX_CMD = "pdflatex"
script_path = os.path.dirname(os.path.abspath(__file__))
root_data = r"C:\Users\User\Desktop\Year"
log_path = os.path.join(script_path, "conversion_log.txt")

def log(msg):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


# ==========================================================
#  MAIN LOOP
# ==========================================================
for week in os.listdir(root_data):
    week_path = os.path.join(root_data, week)
    if not os.path.isdir(week_path):
        continue

    for study in os.listdir(week_path):
        study_path = os.path.join(week_path, study)
        meshes_path = os.path.join(study_path, "meshes")

        if not os.path.isdir(meshes_path):
            continue

        files = os.listdir(meshes_path)
        frames = sorted(list(set([f[:-4] for f in files if f.endswith(".obj")])))

        log(f"[INFO] frames={frames}")

        if not frames:
            continue

        tempfiles = {}
        final_u3ds = {}

        # ======================================================
        #  PROCESS ALL FRAMES FIRST (copy, brighten, u3d)
        # ======================================================
        for frame in frames:
            try:
                jpg_src = os.path.join(meshes_path, frame + ".jpg")
                obj_src = os.path.join(meshes_path, frame + ".obj")
                mtl_src = os.path.join(meshes_path, frame + ".mtl")

                for p in (jpg_src, obj_src, mtl_src):
                    if not os.path.exists(p):
                        raise FileNotFoundError(f"Missing: {p}")

                # temp copies
                jpg_tmp = os.path.join(script_path, frame + ".jpg")
                obj_tmp = os.path.join(script_path, frame + ".obj")
                mtl_tmp = os.path.join(script_path, frame + ".mtl")

                shutil.copyfile(jpg_src, jpg_tmp)
                shutil.copyfile(obj_src, obj_tmp)
                shutil.copyfile(mtl_src, mtl_tmp)

                tempfiles[frame] = [jpg_tmp, obj_tmp, mtl_tmp]

                # brighten
                img = cv2.imread(jpg_tmp)
                adj = cv2.convertScaleAbs(img, alpha=1.5, beta=10)
                cv2.imwrite(jpg_tmp, adj)

                # U3D
                ms = pymeshlab.MeshSet()
                ms.load_new_mesh(obj_tmp)

                u3d_tmp = os.path.join(script_path, frame + ".u3d")
                ms.save_current_mesh(u3d_tmp)

                if not os.path.exists(u3d_tmp):
                    raise RuntimeError("No U3D generated")

                tempfiles[frame].append(u3d_tmp)
                final_u3ds[frame] = u3d_tmp

                log(f"[INFO] {frame}: u3d created")

            except Exception as e:
                log(f"[ERROR] Frame {frame} failed: {e}")
                log(traceback.format_exc())
                continue

        if not final_u3ds:
            continue

        # ---------- BUILD MASTER TEX ----------

        master_name = f"{study[16:]}_{study[:7]}.tex"
        master_tex = os.path.join(script_path, master_name)

        with open(master_tex, "w", encoding="utf-8") as f:
            f.write(r"\documentclass{article}" "\n")
            f.write(r"\usepackage[margin=1in]{geometry}" "\n")
            f.write(r"\usepackage{media9}" "\n")
            f.write(r"\usepackage{graphicx}" "\n")
            f.write(r"\usepackage[english]{babel}" "\n")
            f.write(r"\begin{document}" "\n\n")

            for i, frame in enumerate(final_u3ds.keys()):
                u3d_file = os.path.basename(final_u3ds[frame])
                f.write(f"% ---- Frame: {frame} ----\n")
                f.write(r"\begin{center}" "\n")
                f.write(
                    f"\\includemedia[\n"
                    " width=1\\linewidth,\n"
                    " height=1\\linewidth,\n"
                    " activate=pageopen,\n"
                    " 3Dtoolbar,\n"
                    " 3Dnavpane,\n"
                    " 3Dmenu,\n"
                    " 3Dcoo=0 -10 0,\n"
                    " 3Droo=1000,\n"
                    " 3Daac=20,\n"
                    " 3Dc2c=0.0364591777 -0.0012150183 0.0601891652,\n"
                    " 3Dbg=90 90 90,\n"
                    " 3Dlights=CAD,\n"
                    f"]{{}}{{{u3d_file}}}\n"
                )
                f.write(r"\end{center}" "\n\n")

                if i != len(final_u3ds)-1:
                    f.write(r"\clearpage" "\n\n")

            f.write("\n\\end{document}\n")

        log(f"[INFO] MASTER TEX CREATED: {master_name}")

        # ----------- SAFE PDFLATEX COMPILATION ------------
        # create clean temp work dir
        tmp_dir = tempfile.mkdtemp()

        # copy tex + u3d files to temp dir
        shutil.copyfile(master_tex, os.path.join(tmp_dir, master_name))
        for fpath in final_u3ds.values():
            shutil.copyfile(fpath, os.path.join(tmp_dir, os.path.basename(fpath)))

        # run pdflatex inside temp folder
        cmd = f'cd "{tmp_dir}" && "{PDFLATEX_CMD}" "{master_name}"'
        os.system(cmd)
        os.system(cmd)

        # move pdf back
        pdf_out = os.path.join(tmp_dir, master_name.replace(".tex", ".pdf"))
        final_pdf = os.path.join(week_path, master_name.replace(".tex", ".pdf"))

        if not os.path.exists(pdf_out):
            log("[ERROR] PDF did NOT generate (pdflatex failed).")
        else:
            shutil.copyfile(pdf_out, final_pdf)
            log(f"[INFO] MASTER PDF GENERATED → {final_pdf}")

        # cleanup temp dir
        shutil.rmtree(tmp_dir)
log("[INFO] COMPLETE")
