import datetime
import os
import cProfile
import pstats
import io

from text2phenotype.common.log import operations_logger


def profile_func(my_func, output_path, *args, **kwargs):
    """
    Create cProfiled output for the function passed in
    """
    pr = cProfile.Profile()
    pr.enable()

    # call the function
    outputs = my_func(*args, **kwargs)

    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('tottime')
    ps.print_stats()

    timestamp = datetime.datetime.now().strftime("%Y%d%m_%H%M%S")
    with open(os.path.join(output_path, f'profile_stats_{timestamp}.txt'), 'w+') as f:
        f.write(s.getvalue())
        operations_logger.info(f"Wrote profile stats file to: {f.name}")

    return outputs
