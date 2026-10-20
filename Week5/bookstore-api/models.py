from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

book_authors = db.Table(
    "book_authors",
    db.Column("book_id", db.Integer, db.ForeignKey("books.id"), primary_key=True),
    db.Column("author_id", db.Integer, db.ForeignKey("authors.id"), primary_key=True),
)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "slug": self.slug}


class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(240), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    price_vnd = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)

    category = db.relationship("Category", backref="books")
    authors = db.relationship("Author", secondary=book_authors, backref="books")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "isbn": self.isbn,
            "price_vnd": self.price_vnd,
            "stock": self.stock,
            "category": self.category.to_dict() if self.category else None,
            "authors": [author.to_dict() for author in self.authors],
        }


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
