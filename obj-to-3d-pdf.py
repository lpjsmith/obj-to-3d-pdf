# pip install pymeshlab, confirmed version 2022.2.post3
# pip install opencv-python, confirmed version 4.7.0.68

import os
import shutil

import pymeshlab
import cv2

script_path = os.path.dirname(os.path.abspath(__file__))
path_to_3dmd_data = r'C:\Users\user\Desktop\P\data'
week_folders = os.listdir(path_to_3dmd_data)

for week in week_folders[0:]:
    path_to_week = os.path.join(path_to_3dmd_data, week)
    study_folders = os.listdir(path_to_week)

    for study in study_folders[0:]:
        path_to_meshes = os.path.join(path_to_week, study, "meshes")
        files_list = os.listdir(path_to_meshes)
        new_list = [s[:-4] for s in files_list]
        new_new_list = list(set(new_list))
        print("----")
        frames = [item for item in new_new_list if len(item) != 13 and item != 'mstereo_default']
        
        print(frames)

        for frame in frames:
            jpeg_name = f"{frame}.jpg"
            obj_name = f"{frame}.obj"
            mtl_name = f"{frame}.mtl"

            jpeg_path = os.path.join(path_to_meshes, jpeg_name)
            obj_path = os.path.join(path_to_meshes, obj_name)
            mtl_path = os.path.join(path_to_meshes, mtl_name)

            jpeg_destination_path = os.path.join(script_path, jpeg_name)
            obj_destination_path = os.path.join(script_path, obj_name)
            mtl_destination_path = os.path.join(script_path, mtl_name)

            shutil.copyfile(jpeg_path, jpeg_destination_path)
            shutil.copyfile(obj_path, obj_destination_path)
            shutil.copyfile(mtl_path, mtl_destination_path)


            #INCREASE BRIGHTNESS HERE OF JPEG FIRST
            image = cv2.imread(jpeg_destination_path)
            alpha = 1.5
            beta = 10
            adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
            cv2.imwrite(jpeg_destination_path, adjusted)
            cv2.waitKey()
            cv2.destroyAllWindows()
            
            print(f'{frame}: jpeg brightened')


            #CONVERT obj to u3d
            ms = pymeshlab.MeshSet()
            ms.load_new_mesh(obj_destination_path)
            u3d_path = obj_destination_path[:-4]+'.u3d'
            ms.save_current_mesh(u3d_path)
            
            print(f'{frame}: u3d created')


            #Create the new TEX file
            tex_name = f"{frame}.tex"
            tex_destination_path = os.path.join(script_path, tex_name)
            with open(tex_name, 'w') as f:
                f.write('\\documentclass{article}\n')
                f.write('\\addtolength{\\oddsidemargin}{-1.9in}\n')
                f.write('\\addtolength{\\evensidemargin}{-.875in}\n')
                f.write('\\addtolength{\\textwidth}{1.75in}\n')
                f.write('\\addtolength{\\topmargin}{-1.5in}\n')
                f.write('\\addtolength{\\textheight}{1.75in}\n')
                f.write('\\usepackage{media9}\n')
                f.write('\\usepackage[english]{babel}\n')
                f.write('\\usepackage{animate}\n')
                f.write('\\usepackage{graphicx}\n')
                f.write('\\usepackage{attachfile}\n')
                f.write('\n')
                f.write('\\begin{document}\n')
                f.write('\n')
                f.write(f"\\includemedia[\n       width=1\\linewidth,\n       height=1\\linewidth,\n       scale=1.25,\n       %attachfiles,\n       activate=pageopen,\n       %windowed=false | 10 x 10 @t1,\n       3Dtoolbar,\n       3Dnavpane,\n       3Dmenu,\n       3Dcoo=0 -10 0,\n       3Droo=1000,\n       3Daac=20,\n       3Dc2c=0.03645917773246765 -0.0012150183320045471 0.06018916517496109,\n       3Dbg=90 90 90,\n       3Dlights=CAD,\n       ]{{}}{{{frame}.u3d}} %Model filename\n")
                f.write('\\end{document}\n')
                
            print(f'{frame}: tex created')


            #Run Latex for the current mesh
            os.system(f"pdflatex {tex_name}")
            
            print(f'{frame}: compiling latex done')

            #Move the pdf into the original folder
            pdf_name = f"{frame}.pdf"
            pdf_current_path = os.path.join(script_path, pdf_name)
            pdf_destination_path = os.path.join(script_path, week)
            pdf_dest_filename = os.path.join(script_path, week, pdf_name)
            if not os.path.exists(pdf_destination_path):
                                  os.makedirs(pdf_destination_path, mode=0o777)
            shutil.copyfile(pdf_current_path, pdf_dest_filename)

            print(f"{frame}: pdf moved")

            #clean-up temp files
            extensions = ['.aux', '.jpg', '.log', '.out', '.pdf', '.tex', '.u3d', '.obj', '.mtl']
            for ext in extensions:
                os.remove(f"{jpeg_destination_path[:-4]}{ext}")
            os.remove(f"{jpeg_destination_path[:-10]}tex")
            
            print(f"{frame}: cleanup done")


