from pathlib import Path
import sys

SAVE_SLOT_SIZE = 64  # Tamaño real útil por slot
NUM_SLOTS = 4
EXPECTED_TOTAL = SAVE_SLOT_SIZE * NUM_SLOTS

def load_srm(path):
    data = Path(path).read_bytes()
    if len(data) < EXPECTED_TOTAL:
        raise ValueError(f"SRM file '{path}' is too small: {len(data)} bytes")
    return [data[i * SAVE_SLOT_SIZE:(i + 1) * SAVE_SLOT_SIZE] for i in range(NUM_SLOTS)]

def compare_srms(file1, file2):
    saves1 = load_srm(file1)
    saves2 = load_srm(file2)

    for i in range(NUM_SLOTS):
        print(f"\nSlot {i + 1}:")
        if saves1[i] == saves2[i]:
            print("  ✅ Idénticos")
        else:
            print("  ❌ Diferencias detectadas")
            for j in range(SAVE_SLOT_SIZE):
                if saves1[i][j] != saves2[i][j]:
                    print(f"    Byte {j:02X}: {saves1[i][j]:02X} ≠ {saves2[i][j]:02X}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python srm_compare_util.py <srm1> <srm2>")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]
    compare_srms(file1, file2)
