import random
from enum import Enum

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

MAX_CHARS = 5
MAX_GUESS = 6

class GuessComponent:
    def __init__(self, update_board_handler):
        self.main_box = toga.Box(
            style=Pack(direction='column')
        )

        guess_input_box = toga.Box(
            style=Pack(direction='row')
        )

        guess_label = toga.Label(
            'Guess:',
            style=Pack(
                padding=5,
                padding_top=7.5,
                font_size=12,
            )
        )
        self.guess_input = toga.TextInput(
            style=Pack(
                flex=1,
                font_size=12,
                padding_right=5,
                padding_top=5,
            )
        )

        guess_input_box.add(guess_label)
        guess_input_box.add(self.guess_input)

        self.guess_button = toga.Button(
            'Guess',
            style=Pack(
                flex=1,
                font_size=12,
                padding=5,
            ),
            on_press=update_board_handler
        )

        alphabet: str = ' '.join([chr(i) for i in range(ord('A'), ord('Z')+1)])
        self.alphabet_text = toga.Label(
            alphabet,
            style=Pack(
                flex=1,
                font_size=12,
                padding_left=5,
                padding_right=5,
                padding_top=5,
                padding_bottom=15,
                text_align='center',
            )
        )        

        self.main_box.add(guess_input_box)
        self.main_box.add(self.guess_button)
        self.main_box.add(self.alphabet_text)

class WordBoardComponent:
    def __init__(self):
        self.main_box = toga.Box(
            style=Pack(direction='column')
        )

        for _ in range(MAX_GUESS):
            word_box = toga.Box(
                style=Pack(
                    direction='row',
                    alignment='center',
                    padding=(5, 400),
                )
            )
            for _ in range(MAX_CHARS):
                character = toga.Button(
                    '',
                    style=Pack(
                        flex=1,
                        alignment='center',
                        height=80,
                        padding_left=5,
                        padding_right=5,
                        font_size=12,
                        font_weight='bold'
                    )
                )

                word_box.add(character)

            self.main_box.add(word_box)

    def update_board(self, 
                     row: int, 
                     guess: str, 
                     correct_word: str
                ) -> None:
        
        # For each unique letter in the correct_word, this maps its number
        # of occurrences in the word, e.g. hello => {h: 1, e: 1, l: 2, o: 1}
        histogram: dict[str, int] = dict()
        for char in correct_word:
            try:
                histogram[char] += 1
            except KeyError:
                histogram[char] = 1

        # Color the correctly-guessed letters first...
        for i, char in enumerate(self.main_box.children[row].children):
            guess_char = guess[i]
            
            char.label = guess_char.upper()

            if guess_char == correct_word[i]:
                char.style.background_color = 'green'
                histogram[guess_char] -= 1

        # ...then color the others to prevent coloring conflict.
        for i, char in enumerate(self.main_box.children[row].children):
            guess_char = guess[i]
            
            char.label = guess_char.upper()

            if guess_char in correct_word and histogram[guess_char] > 0:
                char.style.background_color = 'yellow'
                histogram[guess_char] -= 1
            elif guess_char != correct_word[i]:
                char.style.background_color = 'gray'

    def reset(self) -> None:
        for word_box in self.main_box.children:
            for char in word_box.children:
                char.label = ''
                char.style.background_color = 'transparent'

class RestartComponent:
    def __init__(self, restart_game_handler):
        self.main_box = toga.Box(
            style=Pack(direction='column')
        )

        restart_button = toga.Button(
            'Restart',
            style=Pack(
                flex=1,
                font_size=12,
                padding=5,
            ),
            on_press=restart_game_handler
        )

        self.main_box.add(restart_button)

class FileReader:
    def get_words_from_file(self, 
                            app_path: str,
                        ) -> tuple[list[str], list[str]]:

        with open(f'{app_path}/words.txt') as words_file:
            correct_words_list = words_file.read().split('\n')

        with open(f'{app_path}/allowed_guesses.txt') as allowed_guesses_file:
            allowed_words_list = allowed_guesses_file.read().split('\n')

        return (correct_words_list, allowed_words_list)

class Error:
    class ErrorEnum(Enum):
        InvalidGuessLength = 'The guessed word can only be a 5-letter word.'
        GuessNotAlpha      = 'The guessed word can only have alphabetical characters.'
        NotAllowedGuess    = 'The guessed word is not in the list of allowed guesses.'

    def check_for_error(self, 
                        guessed_word, 
                        allowed_words_list
                    ) -> str:
        err = ''
        if len(guessed_word) != 5:
            err = self.ErrorEnum.InvalidGuessLength.value
        elif not guessed_word.isalpha():
            err = self.ErrorEnum.GuessNotAlpha.value
        elif guessed_word.lower() not in allowed_words_list:
            err = self.ErrorEnum.NotAllowedGuess.value

        return err

class WordleClone(toga.App):

    def startup(self):
        self.correct_words_list: list[str] = []
        self.allowed_words_list: list[str] = []
        
        file_reader = FileReader()
        (self.correct_words_list, self.allowed_words_list) = \
                                file_reader.get_words_from_file(self.paths.app)

        self.correct_word: str = random.choice(self.correct_words_list)

        self.game_over = False
        self.guess_count = 0

        self.main_box = toga.Box(
            style=Pack(direction='column')
        )

        self.guess_component = GuessComponent(self.guess_the_word)
        self.wordboard_component = WordBoardComponent()
        self.restart_component = RestartComponent(self.restart_game)

        self.main_box.add(self.guess_component.main_box)
        self.main_box.add(self.wordboard_component.main_box)
        self.main_box.add(self.restart_component.main_box)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_box
        self.main_window.show()

    def guess_the_word(self, handler) -> None:
        guessed_word = self.guess_component.guess_input.value

        error_handler = Error()
        err = error_handler.check_for_error(
                guessed_word, 
                self.allowed_words_list
        )
        if err:
            self.main_window.error_dialog(
                'Error',
                err,
            )
            self.guess_component.guess_input.clear()
            return

        guessed_word = guessed_word.lower()

        self.wordboard_component.update_board(
            self.guess_count, 
            guessed_word,
            self.correct_word,
        )
        self.guess_count += 1

        if self.guess_count == 6:
            self.game_over = True
            self.guess_component.guess_button.enabled = False
            self.guess_component.guess_button.label = 'Game Over'

        if guessed_word == self.correct_word:
            self.main_window.info_dialog(
                'Victory',
                'Hooray! You guessed it correctly!'
            )
            if self.guess_count != 6:
                self.game_over = True
                self.guess_component.guess_button.enabled = False
                self.guess_component.guess_button.label = 'Game Over'
        else:
            if self.game_over:
                self.main_window.error_dialog(
                    'Game Over',
                    'Six incorrect guesses have been made. Game Over.\n\
                     The correct word is {}.'.format(self.correct_word)
                )

    def restart_game(self, handler) -> None:
        self.wordboard_component.reset()
        self.guess_component.guess_input.clear()
        self.correct_word = random.choice(self.correct_words_list)
        self.guess_count = 0
        self.game_over = False
        self.guess_component.guess_button.enabled = True
        self.guess_component.guess_button.label = 'Guess'

def main():
    return WordleClone()
