from flask import request, jsonify, Blueprint,render_template
from app.services.reciepts import upload_and_parse_reciept, get_parsed_reciept
from app.utils.save_reciept_image import save_receipt_image
from app.utils.reciept_parser import reciept_parser


reciepts_bp = Blueprint('reciepts_bp',__name__)

@reciepts_bp.route('/v1/reciepts',methods=['GET','POST'])
def upload_and_parse_reciept_route():
    if request.method == "POST":
        file = request.files.get("reciept")
        instance_id = request.form.get("instance_id")

        if not file:
            return "No file uploaded", 400
        if not instance_id:
            return "No instance ID provided", 400

        resp = upload_and_parse_reciept(instance_id,file)
        
        return jsonify(resp),200
    
    return render_template("upload.html")


@reciepts_bp.route('/v1/reciepts/<id>',methods=['GET'])
def get_parsed_reciept_route(id):
    
    resp = get_parsed_reciept(id)

    return jsonify(resp),200
