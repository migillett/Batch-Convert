import re
from dataclasses import dataclass


@dataclass
class InterlaceDetect:
    tff: int
    bff: int
    progressive: int
    undetermined: int

    @classmethod
    def from_string(self, input_string):
        pattern = r"Parsed_idet_0 @ 0x[0-9a-f]+] Multi frame detection: TFF: (\d+) BFF: (\d+) Progressive: (\d+) Undetermined: (\d+)"
        match = re.search(pattern, input_string)
        if match:
            tff, bff, progressive, undetermined = map(int, match.groups())
            return self(tff, bff, progressive, undetermined)
        else:
            raise ValueError("Invalid input string format")


if __name__ == "__main__":
    # Example usage
    input_string = "[Parsed_idet_0 @ 0x55acfe769800] Multi frame detection: TFF: 35816 BFF: 0 Progressive: 184 Undetermined: 1"
    detection_info = InterlaceDetect.from_string(input_string)

    print(detection_info.__dict__)
