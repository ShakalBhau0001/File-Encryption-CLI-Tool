import os
import base64
import secrets
import warnings
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
from rich.padding import Padding
from rich import box

warnings.filterwarnings("ignore", category=DeprecationWarning)

console = Console()

# Crypto Helper


def derive_key(password: str, salt: bytes, iterations: int = 390000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return base64.urlsafe_b64encode(
        kdf.derive(password.encode("utf-8"))
    )


def print_banner():
    console.clear()
    banner = Text()
    banner.append("███████╗██╗██╗     ███████╗\n",style="bold cyan",)
    banner.append("██╔════╝██║██║     ██╔════╝\n",style="bold cyan",)
    banner.append("█████╗  ██║██║     █████╗\n",style="bold blue",)
    banner.append("██╔══╝  ██║██║     ██╔══╝\n",style="bold blue",)
    banner.append("██║     ██║███████╗███████╗\n",style="bold magenta",)
    banner.append("╚═╝     ╚═╝╚══════╝╚══════╝\n\n",style="bold magenta",)
    banner.append(
        "\n Fernet • PBKDF2-HMAC-SHA256 • Password Protected Files \n",style="dim white"
    )
    console.print(
        Panel(
            Align.center(banner),
            border_style="cyan",
            box=box.DOUBLE_EDGE,
        )
    )


def divider(title=""):
    console.print(
        Rule(title, style="cyan")
    )


def success(message):
    console.print(
        f"\n[bold green]✔[/bold green] {message}\n"
    )


def error(message):
    console.print(
        f"\n[bold red]✘[/bold red] {message}\n"
    )


def info(message):
    console.print(
        f"[bold yellow]ℹ[/bold yellow] {message}"
    )


def prompt_path(label, must_exist=False):
    while True:
        path = Prompt.ask(
            f"[cyan]{label}[/cyan]"
        ).strip()
        if must_exist and not os.path.exists(path):
            error(
                f"File not found : {path}"
            )
        else:
            return path


def prompt_password(label="Password"):
    return Prompt.ask(
        f"[cyan]{label}[/cyan]",
        password=True,
    )


def encrypt_file():
    divider("🔒 Encrypt File")
    input_file = prompt_path(
        "Input File",
        must_exist=True,
    )
    password = prompt_password()
    output_file = Prompt.ask(
        "[cyan]Output File[/cyan]",
        default=input_file + ".enc",
    )
    try:
        with console.status(
            "[bold cyan]Encrypting file...[/bold cyan]",
            spinner="dots",
        ):
            with open(input_file, "rb") as f:
                data = f.read()

            salt = secrets.token_bytes(16)
            key = derive_key(password, salt)
            encrypted = Fernet(key).encrypt(data)
            filename = os.path.basename(
                input_file
            ).encode()

            with open(output_file, "wb") as f:
                f.write(b"FILE")
                f.write(salt)
                f.write(len(filename).to_bytes(2, "big"))
                f.write(filename)
                f.write(encrypted)

        success("File encrypted successfully!")
        console.print(
            Panel.fit(
                f"[green]{output_file}[/green]",
                title="Encrypted File",
                border_style="green",
            )
        )
    except Exception as e:
        error(str(e))


def decrypt_file():
    divider("🔓 Decrypt File")
    input_file = prompt_path(
        "Encrypted File",
        must_exist=True,
    )
    password = prompt_password()
    output_dir = Prompt.ask(
        "[cyan]Output Directory[/cyan]",
        default=os.path.dirname(input_file)
        or ".",
    )

    try:
        with console.status(
            "[bold cyan]Decrypting file...[/bold cyan]",
            spinner="dots",
        ):
            with open(input_file, "rb") as f:
                magic = f.read(4)
                if magic != b"FILE":
                    raise ValueError(
                        "Invalid encrypted file format"
                    )
                salt = f.read(16)
                name_len = int.from_bytes(
                    f.read(2),
                    "big",
                )
                original_name = (
                    f.read(name_len).decode()
                )
                encrypted = f.read()

            key = derive_key(
                password,
                salt,
            )
            decrypted = Fernet(key).decrypt(
                encrypted
            )
            output_path = os.path.join(
                output_dir,
                original_name,
            )

            with open(output_path, "wb") as f:
                f.write(decrypted)

        success("File decrypted successfully!")
        console.print(
            Panel.fit(
                f"[green]{output_path}[/green]",
                title="Recovered File",
                border_style="green",
            )
        )
    except InvalidToken:
        error(
            "Wrong password or corrupted encrypted file."
        )
    except Exception as e:
        error(str(e))


def about():
    divider("ℹ About Toolkit")
    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
    )
    table.add_column("Property", style="yellow")
    table.add_column("Value", style="green")
    table.add_row("Encryption", "Fernet")
    table.add_row("KDF", "PBKDF2-HMAC-SHA256")
    table.add_row("Iterations", "390000")
    table.add_row("Salt", "16 Bytes")
    table.add_row("Output Format", ".enc")
    table.add_row("Integrity", "Authenticated Encryption")
    table.add_row("Language", "Python")
    table.add_row("UI", "Rich CLI")
    console.print(table)


def menu():
    table = Table(
        title="Main Menu",
        box=box.DOUBLE_EDGE,
        border_style="cyan",
    )
    table.add_column(
        "Option",
        justify="center",
        style="bold yellow",
    )
    table.add_column(
        "Action",
        style="green",
    )
    table.add_row("1", "🔒 Encrypt File")
    table.add_row("2", "🔓 Decrypt File")
    table.add_row("3", "ℹ About")
    table.add_row("0", "🚪 Exit")
    console.print(table)


def main():
    while True:
        print_banner()
        menu()
        choice = Prompt.ask(
            "[bold cyan]Select Option[/bold cyan]",
            choices=["1", "2", "3", "0"],
            default="1",
        )
        if choice == "1":
            encrypt_file()
        elif choice == "2":
            decrypt_file()
        elif choice == "3":
            about()
        elif choice == "0":
            console.print()
            console.print(
                Panel(
                    Align.center(
                        Text(
                            "See You Soon ! Stay hidden, stay secure. 🕵️",
                            style="bold cyan",
                        )
                    ),
                    border_style="magenta",
                    box=box.DOUBLE_EDGE,
                )
            )
            break
        if choice != "0":
            Prompt.ask("  [dim]Press Enter to return to menu…[/dim]", default="")

if __name__ == "__main__":
    main()
