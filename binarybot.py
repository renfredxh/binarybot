import time
import binascii
import re
import praw

def bin2ascii(bin_str):
    """Convert a string representing a binary integer to its 
    ASCII equivalent.
    
    >>> bin2ascii('011001100110111101101111')
    'foo'
    """
    # Special non-printed ascii characters will not be included.
    # This includes chars 0 - 32 (excluding 9 and 10 which are \t and \n)
    # and characters 127 - 161 and 173.
    bad_chars = ([i for i in range(0,32) if i not in [9, 10]] + 
                 [i for i in range(127,161)] + [173])
    # ASCII characters are 8-bits long each, so if the length of the string
    # is not divisible by 8, leading zeros are added for padding.
    if len(bin_str) % 8 != 0:
        pad = (8 - (len(bin_str) % 8)) * '0'
        bin_str = pad + bin_str
    # Split the string into smaller byte-sized strings for each character
    chars = [bin_str[i:i+8] for i in range(0,len(bin_str),8)]
    converted = ''
    for byte in chars:
        code = int(byte, 2)
        # Only include printed characters
        if code not in bad_chars:
            converted += chr(int(byte, 2))
    return converted

def parse_binary(text):
    """ Return a list of valid binary strings.
    
    >>> parse_binary('11010011 and  01101100')
    ['11010011', '01101100']
    """
    # Searches for binary strings that are at least 8 characters long. 
    # Two binary strings separated by whitespace are counted as one string.
    bin_re = re.compile(r'\b[01]{8,}[01\s]*\b')
    # Used to exclude decimal-looking numbers and only zeros.
    bad_re = re.compile(r'\b1?0+\b')
    matches = bin_re.findall(text)
    bin_strs = [m for m in matches if not re.match(bad_re, m)]
    bin_strs = [re.sub(r'\s+', '', bs) for bs in bin_strs]
    return bin_strs
    
def reply_to(comment, text):
    t = time.strftime("%m-%d %H:%M:%S", time.localtime())
    # Truncate message if it exceeds max character limit.
    if len(text) >= 10000:
        text = text[:9995] + '...'
    try:
        comment.reply(text)
        with open('bot.log', 'a') as f:
            f.write(comment.id + '\n')
        print("{}: Replied to {}".format(t, comment.id))
    except praw.errors.RateLimitExceeded as e:
        print('{}: Rate Limit exceeded. '
              'Sleeping for {} seconds'.format(t, e.sleep_time))
        # Wait and try again.
        time.sleep(e.sleep_time)
        reply_to(comment, text)
    # Handle and log miscellaneous API exceptions
    except praw.errors.APIException as e:
        with open('bot.log', 'a') as f:
            f.write(comment.id + '\n')
        print("{}: Exception on comment {}, {}".format(t, comment.id, e))

def find_comments(r, subreddit, replied_to):
    """Find comments that contain valid binary strings and reply to them
    with an ASCII translation.
    """
    comments = r.get_comments(subreddit)
    for comment in comments:
        if (comment.id not in replied_to and
                str(comment.author) != USERNAME):
            bin_strs = parse_binary(comment.body)
            reply = ''
            for bin_str in bin_strs:
                ascii = bin2ascii(bin_str)
                # Don't reply to empty or whitespace-only comments
                if ascii != '' and not ascii.isspace():
                    reply += '> {}\n\n'.format(bin_str) 
                    reply += ascii + '\n'
            if reply:
                reply_to(comment, reply)
                replied_to.add(comment.id)

def main():
    r = praw.Reddit('Binary conversion bot by u/SeaCowVengeance v 1.1.'
                    'url: https://github.com/RenfredH04/binarybot')
    r.login(USERNAME, PASSWORD)
    # List of subreddits that will be searched
    subreddits = ['test','funny','AdviceAnimals','ProgrammerHumor','binary']
    # Load in previous replied ids
    try:
        with open('bot.log', 'r') as f:
            replied_to = set([id.rstrip() for id in f])
    except FileNotFoundError:
        replied_to = set()
    # Find new comments 
    for subreddit in subreddits:
        find_comments(r, subreddit, replied_to)
        time.sleep(15)
   
USERNAME = 'BinaryConversionBot'
PASSWORD = ''

if __name__ == '__main__':
    main()
