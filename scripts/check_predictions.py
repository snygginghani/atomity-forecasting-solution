"""Compare regenerated forecasts numerically across platforms and CSV line endings."""
import argparse
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference')
    parser.add_argument('regenerated')
    args = parser.parse_args()
    reference = pd.read_csv(args.reference)
    regenerated = pd.read_csv(args.regenerated)
    pd.testing.assert_frame_equal(reference, regenerated, check_exact=False, rtol=1e-10, atol=1e-10)
    print('Regenerated predictions match the submitted forecast')


if __name__ == '__main__':
    main()
