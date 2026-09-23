import argparse, json, sys
from pathlib import Path
from .blender_runner import BlenderNotFoundError, BlenderRenderError
from .config import load_config
from .dataset_builder import build_dataset
from .doctor import report
from .scene_generator import generate_scenes
from .texture_generator import generate_textures

def parser():
    p=argparse.ArgumentParser(prog="make_3d_train_data"); sub=p.add_subparsers(dest="command",required=True)
    d=sub.add_parser("doctor"); d.add_argument("--blender-bin")
    t=sub.add_parser("textures"); ts=t.add_subparsers(dest="action",required=True); tg=ts.add_parser("generate"); tg.add_argument("--output",default="assets/generated/textures")
    c=sub.add_parser("config"); cs=c.add_subparsers(dest="action",required=True); cv=cs.add_parser("validate"); cv.add_argument("config")
    s=sub.add_parser("scene"); ss=s.add_subparsers(dest="action",required=True); sp=ss.add_parser("preview"); sp.add_argument("--config",required=True); sp.add_argument("--count",type=int,default=1); sp.add_argument("--output")
    g=sub.add_parser("generate"); g.add_argument("--config",required=True); g.add_argument("--blender-bin")
    return p

def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if args.command=="doctor": text,_=report(args.blender_bin); print(text)
        elif args.command=="textures": print(f"Generated {len(generate_textures(args.output))} textures in {args.output}")
        elif args.command=="config": cfg=load_config(args.config); print(f"Configuration OK: {args.config} (mode={cfg['scene']['mode']}, count={cfg['output']['count']})")
        elif args.command=="scene":
            data=[s.to_dict() for s in generate_scenes(load_config(args.config),args.count)]; text=json.dumps(data,ensure_ascii=False,indent=2)
            if args.output: Path(args.output).write_text(text+"\n",encoding="utf-8"); print(f"Wrote {len(data)} scenes to {args.output}")
            else: print(text)
        elif args.command=="generate": print(f"Dataset generated: {build_dataset(load_config(args.config),args.blender_bin)}")
        return 0
    except (ValueError,BlenderNotFoundError,BlenderRenderError) as exc:
        print(f"Error: {exc}",file=sys.stderr); return 2

