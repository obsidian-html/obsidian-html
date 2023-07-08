import traceback

from functools import wraps


def error_addendum(pb):
    return format_error_addendum(compile_error_addendum(pb))


def format_error_addendum(message):
    return "\n\tOBS.HTML EXTRA ERROR INFORMATION:\n\t---------------------------------\n\t" + "\n\t".join([x.strip() for x in message]) + "\n\n"


def compile_error_addendum(pb):
    lut = {
        "action_str": {
            "Unknown": "Tracking information was not provided for this function call",
            "n2m": "Conversion of Obsidian notes to proper Markdown notes",
            "n2m_process_all": "Conversion of Obsidian notes to proper Markdown notes (process all segment)",
            "m2h": "Conversion of markdown notes to html notes",
            "m2h_process_all": "Conversion of markdown notes to html notes (process all segment)",
            "compile_taglist": "Looping over tags to generate tag pages",
        }
    }

    state = pb.state
    message = []

    # Header
    message.append(f"Current action              : {lut['action_str'][state['action']]}")
    if state["action"] == "Unknown":
        return message

    if state["subroutine"] is not None:
        message.append(f"Subroutine                  : {state['subroutine']}")

    # Specifics
    if state["loop_type"] == "note":
        current_note_path = state["current_fo"].path["note"]["file_absolute_path"]
        original_obsidian_folder = pb.paths["original_obsidian_folder"]
        current_obsidian_folder = pb.paths["obsidian_folder"]
        original_path = original_obsidian_folder.joinpath(current_note_path.relative_to(current_obsidian_folder))

    if state["loop_type"] == "md_note":
        current_note_path = state["current_fo"].path["markdown"]["file_absolute_path"]
        original_path = ""

    if state["loop_type"] in ["note", "md_note"]:
        message.append(f"Current note being processed: {current_note_path} ({original_path})")

    return message


def extra_info():
    """This wrapper adds additional data to any raised errors.
    Invoke by decorating a function with `@extra_info()`.
    The wrapped function should have pb as an argument for this wrapper to do anything.
    """

    def dec(f):
        def _decorator(*args, **kwargs):
            res = None
            try:
                # Run wrapped function with original args
                res = f(*args, **kwargs)

            except Exception as ex:
                # get pb object as this should contain our additional info
                pb = None
                for arg in args:
                    if type(arg).__name__ == "PicknickBasket":
                        pb = arg
                if pb is None:
                    for kwarg in kwargs.keys():
                        if type(kwargs[kwarg]).__name__ == "PicknickBasket":
                            pb = kwargs[kwarg]

                # Print original error and traceback
                traceback.print_exception(type(ex), ex, ex.__traceback__)

                # pb is present: provide additional information
                if pb is not None:
                    print(error_addendum(pb))

                # Raising causes double errors to be printed. Just quit like we would with a raise statement
                exit(1)

            return res

        return wraps(f)(_decorator)

    return dec
