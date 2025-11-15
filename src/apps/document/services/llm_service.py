import abc
import json
import logging
import os
from typing import Dict, Any
from google import genai
from google.genai import types
from google.genai.errors import APIError
from src.core.errors.errors import ConflictError

logger = logging.getLogger(__name__)


# Definición de la Interfaz del Motor LLM (Se mantiene inalterada)
class AbstractLLMEngine(abc.ABC):
    """
    Define la interfaz para cualquier motor de IA/LLM que estructure el dictado médico.
    """

    @abc.abstractmethod
    def structure_document(self, document_type: str, transcript: str, clinical_meta: Dict[str, Any]) -> str:
        """
        Toma la transcripción y los metadatos y devuelve el contenido estructurado final.
        """
        raise NotImplementedError


# Implementación de LLM (NUBE): Google Gemini
class GeminiLlmEngine(AbstractLLMEngine):
    """
    Implementación del motor LLM utilizando la API de Google Gemini para estructurar
    documentación clínica.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY_HERE":
            logger.error("GEMINI_API_KEY no configurada.")
            raise ValueError("GEMINI_API_KEY no está configurada. Revise su archivo .env.")

        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Error inicializando cliente Gemini: {e}")
            raise ValueError(f"Error en credenciales Gemini: {e}")

    def _generate_prompt(self, document_type: str, transcript: str, clinical_meta: Dict[str, Any]) -> str:
        """Genera el prompt de sistema y las instrucciones para el LLM."""

        system_instruction = (
            "Usted es un experto en documentación médica que opera bajo estándares HIPAA/ISO. "
            "Su tarea es corregir la transcripción (que puede tener errores fonéticos, ejemplo: 'ante lo poste' por 'anteroposterior') "
            "a español médico **formal y correcto**, y estructurar el contenido en formato **Markdown** según el tipo de documento. "
            "La salida DEBE ser solo el contenido en Markdown, sin preámbulos ni encabezados de tipo 'Aquí está el informe'."
        )

        meta_info = json.dumps(clinical_meta, indent=2)

        if document_type == "radiology_report":
            instructions = (
                "Estructura el dictado como un Informe Radiológico profesional. "
                "Usa los siguientes encabezados en Markdown: "
                "1. **TÉCNICA** (si fue dictada, sino sugiere una estándar). "
                "2. **HALLAZGOS DETALLADOS**. "
                "3. **IMPRESIÓN DIAGNÓSTICA / CONCLUSIÓN**. "
                f"La transcripción es: '{transcript}'."
            )
        elif document_type == "clinical_history":
            instructions = (
                "Estructura el dictado para rellenar una Historia Clínica. "
                "Usa los siguientes encabezados en Markdown: "
                "1. **MOTIVO DE CONSULTA** (Extraer la razón principal). "
                "2. **ANAMNESIS DETALLADA**. "
                "3. **EXAMEN FÍSICO** (Si fue dictado). "
                "4. **PLAN MÉDICO Y TRATAMIENTO**. "
                f"La transcripción es: '{transcript}'."
            )
        else:
            instructions = (
                f"Estructura el dictado para el documento de tipo: {document_type.upper().replace('_', ' ')}. "
                "Corrige el lenguaje a español médico formal. Devuelve el texto corregido bajo un encabezado de **TRANSCRIPCIÓN MÉDICA CORREGIDA**. "
                f"La transcripción es: '{transcript}'."
            )

        final_prompt = f"""
SISTEMA: {system_instruction}

---
DATOS CLÍNICOS ADICIONALES:
{meta_info}
---
INSTRUCCIÓN ESPECÍFICA:
{instructions}
"""
        return final_prompt.strip()

    def structure_document(self, document_type: str, transcript: str, clinical_meta: Dict[str, Any]) -> str:
        """
        Llama a la API de Gemini para obtener el documento estructurado.
        """
        prompt = self._generate_prompt(document_type, transcript, clinical_meta)

        try:
            logger.info(f"Llamando a Gemini (Nube) con modelo {self.model} para {document_type}...")

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.01,  # Baja temperatura para respuestas factuales/estructuradas
                )
            )

            if response.text:
                return response.text
            else:
                raise APIError("Respuesta de Gemini vacía o bloqueada por seguridad.")

        except APIError as e:
            logger.error(f"Error de la API de Gemini: {e}")
            raise ConflictError(f"Error en el motor de IA (Gemini API): No se pudo generar el documento. Detalle: {e}")
        except Exception as e:
            logger.exception(f"Error inesperado al conectar con Gemini: {e}")
            raise ConflictError(f"Error interno al conectar con el servicio LLM. Detalle: {e}")
