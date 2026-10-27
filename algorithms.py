from models import SortEvent


class BubbleSort:
    name = "Bubble Sort"

    def sort(self, numbers):
        for i in range(len(numbers)):
            changed = False
            for j in range(len(numbers) - i - 1):
                yield SortEvent("compare", [j, j + 1])
                if numbers[j] > numbers[j + 1]:
                    numbers[j], numbers[j + 1] = numbers[j + 1], numbers[j]
                    changed = True
                    yield SortEvent("swap", [j, j + 1])
            if not changed:
                break
        yield SortEvent("complete")


class QuickSort:
    name = "Quick Sort"

    def sort(self, numbers):
        yield from self.quick_sort(numbers, 0, len(numbers) - 1)
        yield SortEvent("complete")

    def quick_sort(self, numbers, low, high):
        if low >= high:
            return

        pivot = numbers[high]
        smaller = low
        for current in range(low, high):
            yield SortEvent("compare", [current, high])
            if numbers[current] <= pivot:
                numbers[smaller], numbers[current] = numbers[current], numbers[smaller]
                yield SortEvent("swap", [smaller, current])
                smaller += 1

        numbers[smaller], numbers[high] = numbers[high], numbers[smaller]
        yield SortEvent("swap", [smaller, high])
        yield from self.quick_sort(numbers, low, smaller - 1)
        yield from self.quick_sort(numbers, smaller + 1, high)


class MergeSort:
    name = "Merge Sort"

    def sort(self, numbers):
        yield from self.merge_sort(numbers, 0, len(numbers) - 1)
        yield SortEvent("complete")

    def merge_sort(self, numbers, left, right):
        if left >= right:
            return

        middle = (left + right) // 2
        yield from self.merge_sort(numbers, left, middle)
        yield from self.merge_sort(numbers, middle + 1, right)

        first = numbers[left:middle + 1]
        second = numbers[middle + 1:right + 1]
        i = 0
        j = 0
        position = left

        while i < len(first) and j < len(second):
            yield SortEvent("compare", [left + i, middle + 1 + j])
            if first[i] <= second[j]:
                numbers[position] = first[i]
                i += 1
            else:
                numbers[position] = second[j]
                j += 1
            yield SortEvent("write", [position])
            position += 1

        while i < len(first):
            numbers[position] = first[i]
            yield SortEvent("write", [position])
            i += 1
            position += 1

        while j < len(second):
            numbers[position] = second[j]
            yield SortEvent("write", [position])
            j += 1
            position += 1


class HeapSort:
    name = "Heap Sort"

    def sort(self, numbers):
        size = len(numbers)
        for i in range(size // 2 - 1, -1, -1):
            yield from self.heapify(numbers, size, i)

        for end in range(size - 1, 0, -1):
            numbers[0], numbers[end] = numbers[end], numbers[0]
            yield SortEvent("swap", [0, end])
            yield from self.heapify(numbers, end, 0)
        yield SortEvent("complete")

    def heapify(self, numbers, size, root):
        biggest = root
        left = root * 2 + 1
        right = root * 2 + 2

        if left < size:
            yield SortEvent("compare", [biggest, left])
            if numbers[left] > numbers[biggest]:
                biggest = left
        if right < size:
            yield SortEvent("compare", [biggest, right])
            if numbers[right] > numbers[biggest]:
                biggest = right

        if biggest != root:
            numbers[root], numbers[biggest] = numbers[biggest], numbers[root]
            yield SortEvent("swap", [root, biggest])
            yield from self.heapify(numbers, size, biggest)


ALGORITHMS = {
    "bubble_sort": BubbleSort,
    "quick_sort": QuickSort,
    "merge_sort": MergeSort,
    "heap_sort": HeapSort,
}
