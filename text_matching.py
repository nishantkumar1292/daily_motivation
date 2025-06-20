import re
import difflib
from fuzzywuzzy import fuzz

def normalize_text(text):
    """Normalize text for better matching"""
    # Convert to lowercase
    text = text.lower()

    # Handle common transcript variations
    replacements = {
        # Numbers
        ' twenty ': ' 20 ',
        ' thirty ': ' 30 ',
        ' thirty-one ': ' 31 ',
        ' thirty-two ': ' 32 ',
        ' one ': ' 1 ',
        ' two ': ' 2 ',
        ' three ': ' 3 ',
        ' four ': ' 4 ',
        ' five ': ' 5 ',
        ' six ': ' 6 ',
        ' seven ': ' 7 ',
        ' eight ': ' 8 ',
        ' nine ': ' 9 ',

        # Common contractions and variations
        " i'm ": " i am ",
        " don't ": " do not ",
        " won't ": " will not ",
        " can't ": " cannot ",
        " you're ": " you are ",
        " we're ": " we are ",
        " they're ": " they are ",
        " it's ": " it is ",
        " that's ": " that is ",
        " there's ": " there is ",
        " here's ": " here is ",
        " what's ": " what is ",
        " where's ": " where is ",
        " who's ": " who is ",
        " how's ": " how is ",
        " let's ": " let us ",

        # Remove filler words and hesitations
        ' uh ': ' ',
        ' um ': ' ',
        ' ah ': ' ',
        ' er ': ' ',
        ' hmm ': ' ',
        ' you know ': ' ',
        ' i mean ': ' ',
        ' like ': ' ',
        ' so ': ' ',
        ' well ': ' ',
        ' actually ': ' ',
        ' basically ': ' ',
        ' literally ': ' ',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove extra punctuation but keep sentence structure
    text = re.sub(r'[^\w\s\.\,\!\?]', '', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def extract_words_from_segments(transcription_data):
    """Extract all words with timestamps from transcription segments"""
    all_words = []

    if 'segments' in transcription_data:
        for segment in transcription_data['segments']:
            if 'words' in segment and segment['words']:
                all_words.extend(segment['words'])
            else:
                # Fallback: if no word-level timestamps, use segment-level
                words_in_segment = segment['text'].split()
                segment_duration = segment['end'] - segment['start']
                words_per_second = len(words_in_segment) / segment_duration if segment_duration > 0 else 1

                for i, word in enumerate(words_in_segment):
                    estimated_start = segment['start'] + (i / words_per_second)
                    estimated_end = segment['start'] + ((i + 1) / words_per_second)
                    all_words.append({
                        'word': word,
                        'start': estimated_start,
                        'end': min(estimated_end, segment['end'])
                    })

    return all_words

def find_best_sentence_match(transcription_data, target_sentence, method='fuzzy'):
    """Find the best match for a sentence using multiple approaches"""

    all_words = extract_words_from_segments(transcription_data)

    if not all_words:
        print("No words found in transcription data")
        return None, None

    # Create full transcript text
    full_transcript = ' '.join([word['word'] for word in all_words])

    # Normalize both texts
    normalized_transcript = normalize_text(full_transcript)
    normalized_target = normalize_text(target_sentence)

    print(f"Looking for: '{normalized_target}'")
    print(f"In transcript length: {len(normalized_transcript)} characters")

    if method == 'fuzzy':
        return find_fuzzy_match(all_words, normalized_transcript, normalized_target)
    elif method == 'sliding_window':
        return find_sliding_window_match(all_words, normalized_target)
    elif method == 'sequence_match':
        return find_sequence_match(all_words, normalized_transcript, normalized_target)
    else:
        # Try all methods in order of preference
        methods = ['fuzzy', 'sliding_window', 'sequence_match']
        for m in methods:
            start, end = globals()[f'find_{m.replace("_", "_")}_match'](all_words, normalized_transcript if 'transcript' in locals() else normalized_target, normalized_target)
            if start is not None and end is not None:
                print(f"Found match using {m} method")
                return start, end
        return None, None

def find_fuzzy_match(all_words, full_transcript, target_sentence):
    """Use fuzzy string matching to find the best match"""

    target_words = target_sentence.split()
    target_length = len(target_words)

    if target_length == 0:
        return None, None

    best_ratio = 0
    best_start_idx = -1
    best_end_idx = -1

    # Try different window sizes around the target length
    for window_size in [target_length, target_length + 2, target_length - 1, target_length + 5]:
        if window_size <= 0:
            continue

        for i in range(len(all_words) - window_size + 1):
            window_words = [normalize_text(all_words[j]['word']) for j in range(i, i + window_size)]
            window_text = ' '.join(window_words)

            # Use fuzzy matching
            ratio = fuzz.ratio(window_text, target_sentence)

            if ratio > best_ratio and ratio > 70:  # 70% similarity threshold
                best_ratio = ratio
                best_start_idx = i
                best_end_idx = i + window_size - 1

    if best_start_idx != -1:
        start_time = all_words[best_start_idx]['start']
        end_time = all_words[best_end_idx]['end']
        print(f"Fuzzy match found with {best_ratio}% similarity")
        return start_time, end_time

    return None, None

def find_sliding_window_match(all_words, target_sentence):
    """Use sliding window with flexible word matching"""

    target_words = normalize_text(target_sentence).split()

    if len(target_words) == 0:
        return None, None

    best_score = 0
    best_start_idx = -1
    best_end_idx = -1

    # Try different window sizes
    for window_size in range(len(target_words), min(len(target_words) + 10, len(all_words) + 1)):
        for i in range(len(all_words) - window_size + 1):
            window_words = [normalize_text(all_words[j]['word']) for j in range(i, i + window_size)]

            # Calculate match score
            score = calculate_word_match_score(target_words, window_words)

            if score > best_score and score > 0.6:  # 60% match threshold
                best_score = score
                best_start_idx = i
                best_end_idx = i + window_size - 1

    if best_start_idx != -1:
        start_time = all_words[best_start_idx]['start']
        end_time = all_words[best_end_idx]['end']
        print(f"Sliding window match found with score {best_score:.2f}")
        return start_time, end_time

    return None, None

def find_sequence_match(all_words, full_transcript, target_sentence):
    """Use sequence matching to find similar text blocks"""

    matcher = difflib.SequenceMatcher(None, full_transcript, target_sentence)
    match = matcher.find_longest_match(0, len(full_transcript), 0, len(target_sentence))

    if match.size < len(target_sentence) * 0.6:  # At least 60% of target should match
        return None, None

    # Find word indices for the matched substring
    matched_text = full_transcript[match.a:match.a + match.size]

    # Count words before the match to find start index
    words_before_match = len(full_transcript[:match.a].split())
    words_in_match = len(matched_text.split())

    if words_before_match < len(all_words) and words_before_match + words_in_match <= len(all_words):
        start_time = all_words[words_before_match]['start']
        end_idx = min(words_before_match + words_in_match - 1, len(all_words) - 1)
        end_time = all_words[end_idx]['end']

        print(f"Sequence match found: {match.size}/{len(target_sentence)} characters")
        return start_time, end_time

    return None, None

def calculate_word_match_score(target_words, window_words):
    """Calculate how well window_words matches target_words"""
    if not target_words or not window_words:
        return 0

    matches = 0
    target_idx = 0

    for window_word in window_words:
        if target_idx < len(target_words) and window_word == target_words[target_idx]:
            matches += 1
            target_idx += 1

    # Score based on how many target words we found in order
    return matches / len(target_words)

def find_robust_timestamps(transcription_data, sentence_text, buffer_seconds=1):
    """
    Robust timestamp finding with multiple fallback methods
    """
    print(f"\n🔍 Searching for: '{sentence_text[:50]}...'")

    # Try multiple methods
    methods = ['fuzzy', 'sliding_window', 'sequence_match']

    for method in methods:
        print(f"Trying {method} method...")
        start_time, end_time = find_best_sentence_match(transcription_data, sentence_text, method)

        if start_time is not None and end_time is not None:
            # Add buffer
            start_time = max(0, start_time - buffer_seconds)
            end_time = end_time + buffer_seconds

            print(f"✅ Found using {method}: {start_time:.2f}s - {end_time:.2f}s")
            return start_time, end_time
        else:
            print(f"❌ {method} method failed")

    # Last resort: try partial matching
    print("Trying partial matching...")
    return find_partial_match(transcription_data, sentence_text, buffer_seconds)

def find_partial_match(transcription_data, sentence_text, buffer_seconds=1):
    """Find partial matches by looking for key phrases"""

    all_words = extract_words_from_segments(transcription_data)
    full_text = ' '.join([word['word'] for word in all_words])

    # Extract key phrases from the sentence
    normalized_sentence = normalize_text(sentence_text)
    words = normalized_sentence.split()

    # Try to find significant chunks (3+ words)
    for chunk_size in [5, 4, 3]:
        for i in range(len(words) - chunk_size + 1):
            chunk = ' '.join(words[i:i + chunk_size])

            # Look for this chunk in the transcript
            normalized_transcript = normalize_text(full_text)
            if chunk in normalized_transcript:
                # Find word position
                chunk_start_pos = normalized_transcript.find(chunk)
                words_before = len(normalized_transcript[:chunk_start_pos].split())

                if words_before < len(all_words):
                    start_time = max(0, all_words[words_before]['start'] - buffer_seconds)

                    # Estimate end time
                    chunk_word_count = len(chunk.split())
                    end_word_idx = min(words_before + chunk_word_count + 5, len(all_words) - 1)  # Add some buffer words
                    end_time = all_words[end_word_idx]['end'] + buffer_seconds

                    print(f"✅ Partial match found for '{chunk}': {start_time:.2f}s - {end_time:.2f}s")
                    return start_time, end_time

    print("❌ No partial matches found")
    return None, None
